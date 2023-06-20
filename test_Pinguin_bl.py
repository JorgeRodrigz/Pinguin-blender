import pytest

from Pinguin_bl import cross_product_3d

def test_cross_product_3d():
    vector1 = [1, 2, 3]
    vector2 = [4, 5, 6]
    expected_result = [-3, 6, -3]
    assert cross_product_3d(vector1, vector2) == expected_result

    vector1 = [0, 0, 0]
    vector2 = [1, 2, 3]
    expected_result = [0, 0, 0]
    assert cross_product_3d(vector1, vector2) == expected_result

    vector1 = [2, -3, 1]
    vector2 = [4, 1, 2]
    expected_result = [-5, 6, 11]
    assert cross_product_3d(vector1, vector2) == expected_result

    # Add more test cases as needed

