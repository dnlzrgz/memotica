def sm2(n: int, ef: float, i: int, q: int) -> tuple[int, float, int]:
    """
    A simple implementation of the SuperMemo 2 (SM2) algorithm in Python.

    :param n: Number of times the card has been successfully recalled.
    :param ef: The easiness factor.
    :param i: Inter-repetition interval.
    :param q: Quality of the response.

    :return tuple[int, float, int]: a tuple containing the updated values of n, ef and the inter-repetition interval, which represents days.
    """

    if q >= 3:
        if n == 0:
            i = 1
        elif n == 1:
            i = 6
        else:
            i = round(i * ef)

        n += 1
    else:
        n = 0
        i = 1

    diff = 5 - q
    ef = ef + (0.1 - diff * (0.08 + diff * 0.002))
    ef = max(ef, 1.3)

    return (n, ef, i)
