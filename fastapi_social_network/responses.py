from typing import Set, Dict
from . import schemas

ERROR_RESPONSE = {"model": schemas.ResponseMessage}


def gen_errors_responses(codes: Set[int]) -> Dict[int, Dict]:
    return {code: ERROR_RESPONSE for code in codes}


RESPONSES_400 = gen_errors_responses({400})
RESPONSES_401 = gen_errors_responses({401})
RESPONSES_403 = gen_errors_responses({403})
RESPONSES_404 = gen_errors_responses({404})
RESPONSES_401_404 = gen_errors_responses({401, 404})
RESPONSES_401_403_404 = gen_errors_responses({401, 403, 404})
