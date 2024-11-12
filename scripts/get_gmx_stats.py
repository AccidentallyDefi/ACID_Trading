from utils import _set_paths

print("Setting paths...")
_set_paths()

from gmx_python_sdk.scripts.v2.get.get_available_liquidity import GetAvailableLiquidity
from gmx_python_sdk.scripts.v2.get.get_borrow_apr import GetBorrowAPR
from gmx_python_sdk.scripts.v2.get.get_claimable_fees import GetClaimableFees
from gmx_python_sdk.scripts.v2.get.get_contract_balance import GetPoolTVL as ContractTVL
from gmx_python_sdk.scripts.v2.get.get_funding_apr import GetFundingFee
from gmx_python_sdk.scripts.v2.get.get_gm_prices import GMPrices
from gmx_python_sdk.scripts.v2.get.get_markets import Markets
from gmx_python_sdk.scripts.v2.get.get_open_interest import OpenInterest
from gmx_python_sdk.scripts.v2.get.get_oracle_prices import OraclePrices
from gmx_python_sdk.scripts.v2.get.get_pool_tvl import GetPoolTVL
from gmx_python_sdk.scripts.v2.get.get_glv_stats import GlvStats

from gmx_python_sdk.scripts.v2.gmx_utils import ConfigManager


class GetGMXv2Stats:

    def __init__(self, config, to_json, to_csv):
        print("Initializing GetGMXv2Stats...")
        self.config = config
        self.to_json = to_json
        self.to_csv = to_csv
        print(f"Initialized GetGMXv2Stats with to_json={self.to_json} and to_csv={self.to_csv}")

    def get_available_liquidity(self):
        print("Fetching available liquidity...")
        result = GetAvailableLiquidity(self.config).get_data(to_csv=self.to_csv, to_json=self.to_json)
        print("Fetched available liquidity.")
        return result

    def get_borrow_apr(self):
        print("Fetching borrow APR...")
        result = GetBorrowAPR(self.config).get_data(to_csv=self.to_csv, to_json=self.to_json)
        print("Fetched borrow APR.")
        return result

    def get_claimable_fees(self):
        print("Fetching claimable fees...")
        result = GetClaimableFees(self.config).get_data(to_csv=self.to_csv, to_json=self.to_json)
        print("Fetched claimable fees.")
        return result

    def get_contract_tvl(self):
        print("Fetching contract TVL...")
        result = ContractTVL(self.config).get_pool_balances(to_json=self.to_json)
        print("Fetched contract TVL.")
        return result

    def get_funding_apr(self):
        print("Fetching funding APR...")
        result = GetFundingFee(self.config).get_data(to_csv=self.to_csv, to_json=self.to_json)
        print("Fetched funding APR.")
        return result

    def get_gm_price(self):
        print("Fetching GM prices...")
        result = GMPrices(self.config).get_price_traders(to_csv=self.to_csv, to_json=self.to_json)
        print("Fetched GM prices.")
        return result

    def get_available_markets(self):
        print("Fetching available markets...")
        result = Markets(self.config).get_available_markets()
        print("Fetched available markets.")
        return result

    def get_open_interest(self):
        print("Fetching open interest...")
        result = OpenInterest(self.config).get_data(to_csv=self.to_csv, to_json=self.to_json)
        print("Fetched open interest.")
        return result

    def get_oracle_prices(self):
        print("Fetching oracle prices...")
        result = OraclePrices(self.config.chain).get_recent_prices()
        print("Fetched oracle prices.")
        return result

    def get_pool_tvl(self):
        print("Fetching pool TVL...")
        result = GetPoolTVL(self.config).get_pool_balances(to_csv=self.to_csv, to_json=self.to_json)
        print("Fetched pool TVL.")
        return result

    def get_glv_stats(self):
        print("Fetching GLV stats...")
        result = GlvStats(self.config).get_glv_stats()
        print("Fetched GLV stats.")
        return result


if __name__ == "__main__":

    print("Setting up main execution...")
    to_json = True
    to_csv = True

    print("Configuring GMX with arbitrum chain...")
    config = ConfigManager(chain='arbitrum')
    config.set_config()
    print("Configuration complete.")

    stats_object = GetGMXv2Stats(
        config=config,
        to_json=to_json,
        to_csv=to_csv
    )
    print("GetGMXv2Stats instance created.")

    print("Fetching markets...")
    markets = stats_object.get_available_markets()
    print("Markets fetched:", markets)

    print("Fetching available liquidity...")
    liquidity = stats_object.get_available_liquidity()
    print("Available liquidity:", liquidity)

    print("Fetching borrow APR...")
    borrow_apr = stats_object.get_borrow_apr()
    print("Borrow APR:", borrow_apr)

    print("Fetching claimable fees...")
    claimable_fees = stats_object.get_claimable_fees()
    print("Claimable fees:", claimable_fees)

    print("Fetching contract TVL...")
    contract_tvl = stats_object.get_contract_tvl()
    print("Contract TVL:", contract_tvl)

    print("Fetching funding APR...")
    funding_apr = stats_object.get_funding_apr()
    print("Funding APR:", funding_apr)

    print("Fetching GM prices...")
    gm_prices = stats_object.get_gm_price()
    print("GM prices:", gm_prices)

    print("Fetching open interest...")
    open_interest = stats_object.get_open_interest()
    print("Open interest:", open_interest)

    print("Fetching oracle prices...")
    oracle_prices = stats_object.get_oracle_prices()
    print("Oracle prices:", oracle_prices)

    print("Fetching pool TVL...")
    pool_tvl = stats_object.get_pool_tvl()
    print("Pool TVL:", pool_tvl)

    print("Fetching GLV stats...")
    glv_price = stats_object.get_glv_stats()
    print("GLV stats:", glv_price)

    print("Execution completed.")
