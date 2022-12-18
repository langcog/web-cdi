import numpy as np


def write_to_zip(x, zf, vocab_start):
    curr_name = "{0}_S{1}_{2}".format(x["study_name"], x["subject_id"], x["repeat_num"])
    vocab_string = (
        x[vocab_start:].to_string(header=False, index=False).replace("\n", "")
    )
    demo_string = ("{!s:<25}" * (vocab_start)).format(
        *x[0:vocab_start].replace(r"", np.nan, regex=True)
    )
    string_to_write = demo_string + vocab_string
    zf.writestr("{}.txt".format(curr_name), string_to_write)
