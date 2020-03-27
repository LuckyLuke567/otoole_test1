from io import StringIO
from textwrap import dedent

from pytest import mark

import pandas as pd

from otoole.results.convert import (
    convert_cbc_to_dataframe,
    convert_dataframe_to_csv,
    process_line,
)


class TestCbcSoltoDataFrame:

    test_data = [
        (
            dedent(
                """Optimal - objective value 4483.96932237
                             1 TotalDiscountedCost(SIMPLICITY,2015)                                                   187.01576                       0
                             2 TotalDiscountedCost(SIMPLICITY,2016)                                                   183.30788                       0
                             3 TotalDiscountedCost(SIMPLICITY,2017)                                                   181.05465                       0
                             4 TotalDiscountedCost(SIMPLICITY,2018)                                                   218.08923                       0
                             5 TotalDiscountedCost(SIMPLICITY,2019)                                                   193.85792                       0
                             6 TotalDiscountedCost(SIMPLICITY,2020)                                                   233.79202                       0

                         """
            ),
            pd.DataFrame(
                data=[
                    ["TotalDiscountedCost", "SIMPLICITY,2015", 187.01576],
                    ["TotalDiscountedCost", "SIMPLICITY,2016", 183.30788],
                    ["TotalDiscountedCost", "SIMPLICITY,2017", 181.05465],
                    ["TotalDiscountedCost", "SIMPLICITY,2018", 218.08923],
                    ["TotalDiscountedCost", "SIMPLICITY,2019", 193.85792],
                    ["TotalDiscountedCost", "SIMPLICITY,2020", 233.79202],
                ],
                columns=["Variable", "Index", "Value"],
            ),
        )
    ]

    @mark.parametrize("cbc_input,expected", test_data, ids=["TotalDiscountedCost"])
    def test_read_cbc_to_dataframe(self, cbc_input, expected):
        with StringIO(cbc_input) as file_buffer:
            actual = convert_cbc_to_dataframe(file_buffer)
            pd.testing.assert_frame_equal(actual, expected)


class TestCbctoCsv:
    test_data = [
        (
            pd.DataFrame(
                data=[
                    ["TotalDiscountedCost", "SIMPLICITY,2015", 187.01576],
                    ["TotalDiscountedCost", "SIMPLICITY,2016", 183.30788],
                    ["TotalDiscountedCost", "SIMPLICITY,2017", 181.05465],
                    ["TotalDiscountedCost", "SIMPLICITY,2018", 218.08923],
                    ["TotalDiscountedCost", "SIMPLICITY,2019", 193.85792],
                    ["TotalDiscountedCost", "SIMPLICITY,2020", 233.79202],
                ],
                columns=["Variable", "Index", "Value"],
            ),
            (
                {
                    "TotalDiscountedCost": pd.DataFrame(
                        data=[
                            ["SIMPLICITY", 2015, 187.01576],
                            ["SIMPLICITY", 2016, 183.30788],
                            ["SIMPLICITY", 2017, 181.05465],
                            ["SIMPLICITY", 2018, 218.08923],
                            ["SIMPLICITY", 2019, 193.85792],
                            ["SIMPLICITY", 2020, 233.79202],
                        ],
                        columns=["REGION", "YEAR", "VALUE"],
                    ).set_index(["REGION", "YEAR"])
                }
            ),
        ),
        (
            pd.DataFrame(
                data=[
                    ["AnnualEmissions", "REGION,CO2,2017", 137958.8400384134],
                    ["AnnualEmissions", "REGION,CO2,2018", 305945.3841061913],
                    ["AnnualEmissions", "REGION,CO2,2019", 626159.9611543404],
                ],
                columns=["Variable", "Index", "Value"],
            ),
            {
                "AnnualEmissions": pd.DataFrame(
                    data=[
                        ["REGION", "CO2", 2017, 137958.8400384134],
                        ["REGION", "CO2", 2018, 305945.3841061913],
                        ["REGION", "CO2", 2019, 626159.9611543404],
                    ],
                    columns=["REGION", "EMISSION", "YEAR", "VALUE"],
                ).set_index(["REGION", "EMISSION", "YEAR"])
            },
        ),
    ]

    @mark.parametrize(
        "df_input,expected", test_data, ids=["TotalDiscountedCost", "AnnualEmissions"]
    )
    def test_convert_cbc_to_csv(self, df_input, expected):

        actual = convert_dataframe_to_csv(df_input)
        assert isinstance(actual, dict)
        for name, df in actual.items():
            pd.testing.assert_frame_equal(df, expected[name])


class TestCplexToCsv:

    test_data = [
        (
            "AnnualFixedOperatingCost	REGION	AOBACKSTOP	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0		",
            [],
        ),
        (
            "AnnualFixedOperatingCost	REGION	CDBACKSTOP	0.0	0.0	137958.8400384134	305945.38410619126	626159.9611543404	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0",
            [
                'AnnualFixedOperatingCost,"REGION,CDBACKSTOP,2017",137958.8400384134\n',
                'AnnualFixedOperatingCost,"REGION,CDBACKSTOP,2018",305945.3841061913\n',
                'AnnualFixedOperatingCost,"REGION,CDBACKSTOP,2019",626159.9611543404\n',
            ],
        ),
        (
            """RateOfActivity	REGION	S1D1	CGLFRCFURX	1	0.0	0.0	0.0	0.0	0.0	0.3284446367303371	0.3451714779880536	0.3366163200621617	0.3394945166233896	0.3137488154250392	0.28605725055560716	0.2572505015401749	0.06757558148965725	0.0558936625751148	0.04330608461292407	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0""",
            [
                'RateOfActivity,"REGION,S1D1,CGLFRCFURX,1,2020",0.3284446367303371\n',
                'RateOfActivity,"REGION,S1D1,CGLFRCFURX,1,2021",0.3451714779880536\n',
                'RateOfActivity,"REGION,S1D1,CGLFRCFURX,1,2022",0.3366163200621617\n',
                'RateOfActivity,"REGION,S1D1,CGLFRCFURX,1,2023",0.3394945166233896\n',
                'RateOfActivity,"REGION,S1D1,CGLFRCFURX,1,2024",0.3137488154250392\n',
                'RateOfActivity,"REGION,S1D1,CGLFRCFURX,1,2025",0.28605725055560716\n',
                'RateOfActivity,"REGION,S1D1,CGLFRCFURX,1,2026",0.2572505015401749\n',
                'RateOfActivity,"REGION,S1D1,CGLFRCFURX,1,2027",0.06757558148965725\n',
                'RateOfActivity,"REGION,S1D1,CGLFRCFURX,1,2028",0.0558936625751148\n',
                'RateOfActivity,"REGION,S1D1,CGLFRCFURX,1,2029",0.04330608461292407\n',
            ],
        ),
    ]

    @mark.parametrize("cplex_input,expected", test_data)
    def test_convert_from_cplex_to_cbc(self, cplex_input, expected):

        actual = process_line(cplex_input, 2015, 2070, "csv")
        assert actual == expected


class TestCplexToCbc:

    test_data = [
        (
            "AnnualFixedOperatingCost	REGION	AOBACKSTOP	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0		",
            [],
        ),
        (
            "AnnualFixedOperatingCost	REGION	CDBACKSTOP	0.0	0.0	137958.8400384134	305945.38410619126	626159.9611543404	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0",
            [
                "0 AnnualFixedOperatingCost(REGION,CDBACKSTOP,2017) 137958.8400384134 0\n",
                "0 AnnualFixedOperatingCost(REGION,CDBACKSTOP,2018) 305945.3841061913 0\n",
                "0 AnnualFixedOperatingCost(REGION,CDBACKSTOP,2019) 626159.9611543404 0\n",
            ],
        ),
        (
            """RateOfActivity	REGION	S1D1	CGLFRCFURX	1	0.0	0.0	0.0	0.0	0.0	0.3284446367303371	0.3451714779880536	0.3366163200621617	0.3394945166233896	0.3137488154250392	0.28605725055560716	0.2572505015401749	0.06757558148965725	0.0558936625751148	0.04330608461292407	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0	0.0""",
            [
                "0 RateOfActivity(REGION,S1D1,CGLFRCFURX,1,2020) 0.3284446367303371 0\n",
                "0 RateOfActivity(REGION,S1D1,CGLFRCFURX,1,2021) 0.3451714779880536 0\n",
                "0 RateOfActivity(REGION,S1D1,CGLFRCFURX,1,2022) 0.3366163200621617 0\n",
                "0 RateOfActivity(REGION,S1D1,CGLFRCFURX,1,2023) 0.3394945166233896 0\n",
                "0 RateOfActivity(REGION,S1D1,CGLFRCFURX,1,2024) 0.3137488154250392 0\n",
                "0 RateOfActivity(REGION,S1D1,CGLFRCFURX,1,2025) 0.28605725055560716 0\n",
                "0 RateOfActivity(REGION,S1D1,CGLFRCFURX,1,2026) 0.2572505015401749 0\n",
                "0 RateOfActivity(REGION,S1D1,CGLFRCFURX,1,2027) 0.06757558148965725 0\n",
                "0 RateOfActivity(REGION,S1D1,CGLFRCFURX,1,2028) 0.0558936625751148 0\n",
                "0 RateOfActivity(REGION,S1D1,CGLFRCFURX,1,2029) 0.04330608461292407 0\n",
            ],
        ),
    ]

    @mark.parametrize("cplex_input,expected", test_data)
    def test_convert_from_cplex_to_cbc(self, cplex_input, expected):

        actual = process_line(cplex_input, 2015, 2070, "cbc")
        assert actual == expected
