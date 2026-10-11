/**
 * Web-CDI in-browser CAT engine.
 *
 * Reproduces the behavior of the R backend (langcog/cdi-cat-api, mirtCAT
 * with criteria='MI', method='ML', min 25 / max 50 items, min SEM 0.15):
 *  - theta via jsCat maximum-likelihood once the response pattern contains
 *    both a yes and a no;
 *  - before that, a MAP estimate (posterior mode, N(0,1) prior), which is
 *    what mirtCAT silently uses for unmixed patterns;
 *  - item selection by maximum Fisher information at the current theta;
 *  - SE = 1/sqrt(total Fisher information at theta).
 *
 * Validated against freshly generated mirtCAT sequences for all five
 * languages (theta within 0.0024, item selection 246/246, identical stop
 * points) — see cdi_forms/cat_forms/jscat/test-engine.mjs.
 *
 * Item indices are 1-based, matching the R API and the indices stored in
 * CatResponse.administered_items.
 */
import { Cat } from "@bdelab/jscat";

/** MAP estimate: posterior mode with N(0,1) prior, golden-section search. */
function map4pl(zetas, resps) {
  const logPost = (t) => {
    let lp = -0.5 * t * t;
    for (let i = 0; i < zetas.length; i++) {
      const { a, b, c, d } = zetas[i];
      const p = c + (d - c) / (1 + Math.exp(-a * (t - b)));
      lp += resps[i] ? Math.log(p) : Math.log(1 - p);
    }
    return lp;
  };
  let lo = -6, hi = 6;
  const gr = (Math.sqrt(5) - 1) / 2;
  let x1 = hi - gr * (hi - lo), x2 = lo + gr * (hi - lo);
  let f1 = logPost(x1), f2 = logPost(x2);
  for (let k = 0; k < 80; k++) {
    if (f1 < f2) { lo = x1; x1 = x2; f1 = f2; x2 = lo + gr * (hi - lo); f2 = logPost(x2); }
    else { hi = x2; x2 = x1; f2 = f1; x1 = hi - gr * (hi - lo); f1 = logPost(x1); }
  }
  return (lo + hi) / 2;
}

/** Fisher information of a 4PL item at theta. */
function fisherInfo(item, t) {
  const { a, b, c, d } = item;
  const e = Math.exp(-a * (t - b));
  const p = c + (d - c) / (1 + e);
  const pprime = (a * (d - c) * e) / ((1 + e) * (1 + e));
  return (pprime * pprime) / (p * (1 - p));
}

/**
 * @param params  parsed <CODE>.json bank: {design, defaultStartAge, startItems, items}
 * @param state   {items: number[], responses: (0|1|boolean)[]} — administered so far
 */
export function createEngine(params, state) {
  const bank = new Map(params.items.map((it) => [it.index, it]));
  const administered = (state && state.items ? state.items : []).slice();
  const responses = (state && state.responses ? state.responses : []).map((r) =>
    r ? 1 : 0
  );

  function estimate() {
    if (!administered.length) return { theta: 0, se: Infinity };
    const zetas = administered.map((i) => bank.get(i));
    const mixed = responses.includes(0) && responses.includes(1);
    let theta;
    if (mixed) {
      const cat = new Cat({ method: "MLE" });
      cat.updateAbilityEstimate(zetas, responses);
      theta = cat.theta;
    } else {
      theta = map4pl(zetas, responses);
    }
    let info = 0;
    for (const z of zetas) info += fisherInfo(z, theta);
    return { theta, se: info > 0 ? 1 / Math.sqrt(info) : Infinity };
  }

  return {
    /** The age-based first item (only meaningful before any responses). */
    startItem(ageMonths) {
      const si =
        params.startItems[String(ageMonths)] ||
        params.startItems[String(params.defaultStartAge)];
      return { index: si.index, definition: si.definition };
    },

    /** Record an answer for an item (1-based index). */
    record(index, response) {
      administered.push(index);
      responses.push(response ? 1 : 0);
    },

    /**
     * Current state: theta/SE, and either the next item to show or
     * stop=true when the design's stopping rule is met.
     */
    next() {
      const { theta, se } = estimate();
      const n = administered.length;
      const { minItems, maxItems, minSEM } = params.design;
      if ((n >= minItems && se <= minSEM) || n >= maxItems) {
        return { stop: true, curTheta: theta, se, count: n };
      }
      if (n === 0) {
        const si = this.startItem(params.defaultStartAge);
        return { stop: false, ...si, curTheta: theta, se, count: n };
      }
      const seen = new Set(administered);
      let best = null, bestInfo = -Infinity;
      for (const it of params.items) {
        if (seen.has(it.index)) continue;
        const info = fisherInfo(it, theta);
        if (info > bestInfo) { bestInfo = info; best = it; }
      }
      return {
        stop: false,
        index: best.index,
        definition: best.definition,
        curTheta: theta,
        se,
        count: n,
      };
    },

    state() {
      return { items: administered.slice(), responses: responses.slice() };
    },
  };
}
