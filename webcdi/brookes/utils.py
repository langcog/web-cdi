import random
import string

# Where to buy an access code, per chargeable instrument family. Brookes sells
# one Web-CDI access product per family (listed on brookespublishing.com/
# product/cdi/). Keyed by family name rather than pk so it holds across
# deployments (the EU server has its own database). Anything not listed falls
# back to the general Web-CDI page.
BROOKES_WEBCDI_URL = "https://brookespublishing.com/webcdi/"
BROOKES_SUPPORT_URL = "https://support.brookespublishing.com/"
BROOKES_PRODUCT_URLS = {
    "English (American/Canadian) Long": "https://products.brookespublishing.com/MacArthur-Bates-Web-CDI-English-Access-P1488.aspx",
    "English (American/Canadian) CAT": "https://products.brookespublishing.com/MacArthur-Bates-Web-CDI-English-Computer-Adaptive-Testing-CAT-Access-P1491.aspx",
    "Spanish (Mexican) Long": "https://products.brookespublishing.com/MacArthur-Bates-Web-CDI-Spanish-Access-P1489.aspx",
    "Spanish (Mexican) CAT": "https://products.brookespublishing.com/MacArthur-Bates-Web-CDI-Spanish-Computer-Adaptive-Testing-CAT-Access-P1490.aspx",
}


def purchase_url_for(instrument_family):
    """Brookes page where a code for this family is sold (general page if unknown)."""
    name = getattr(instrument_family, "name", None)
    return BROOKES_PRODUCT_URLS.get(name, BROOKES_WEBCDI_URL)


def create_brookes_code(length=15):
    # choose from all lowercase letter
    letters = string.ascii_uppercase + string.digits
    letters.replace("I", "").replace("O", "")
    result_str = "".join(random.choice(letters) for i in range(length))
    return result_str
