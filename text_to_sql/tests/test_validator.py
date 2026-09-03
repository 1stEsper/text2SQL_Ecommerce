import unittest

from text_to_sql.validator import validate_sql


class ValidateSqlTests(unittest.TestCase):
    def test_allows_approved_gold_query_and_adds_limit(self):
        sql = validate_sql(
            "select month_start, revenue from gold.mart_sales_monthly"
        )
        self.assertIn("LIMIT 100", sql)

    def test_allows_cte_over_approved_relation(self):
        sql = validate_sql(
            """
            with monthly as (
                select * from gold.mart_sales_monthly
            )
            select * from monthly
            """
        )
        self.assertIn("gold.mart_sales_monthly", sql)

    def test_caps_large_limit(self):
        sql = validate_sql(
            "select * from gold.mart_sales_daily limit 1000"
        )
        self.assertIn("LIMIT 100", sql)
        self.assertNotIn("LIMIT 1000", sql)

    def test_blocks_multiple_statements(self):
        with self.assertRaisesRegex(ValueError, "Exactly one"):
            validate_sql(
                "select * from gold.mart_sales_daily; "
                "select * from gold.mart_sales_monthly"
            )

    def test_blocks_write_statement(self):
        with self.assertRaisesRegex(ValueError, "forbidden"):
            validate_sql("delete from gold.mart_sales_daily")

    def test_blocks_bronze_relation(self):
        with self.assertRaisesRegex(ValueError, "gold schema"):
            validate_sql("select * from bronze.ecom_sales")

    def test_blocks_unqualified_relation(self):
        with self.assertRaisesRegex(ValueError, "gold schema"):
            validate_sql("select * from mart_sales_daily")

    def test_blocks_non_allowlisted_gold_relation(self):
        with self.assertRaisesRegex(ValueError, "not approved"):
            validate_sql("select * from gold.mart_customer_360")

    def test_blocks_external_file_function(self):
        with self.assertRaises(ValueError):
            validate_sql("select * from read_csv('/tmp/private.csv')")


if __name__ == "__main__":
    unittest.main()

