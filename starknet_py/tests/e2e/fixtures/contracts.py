# pylint: disable=redefined-outer-name
from typing import List

import pytest
import pytest_asyncio

from starknet_py.common import create_compiled_contract
from starknet_py.compile.compiler import create_contract_class
from starknet_py.constants import FEE_CONTRACT_ADDRESS
from starknet_py.contract import Contract
from starknet_py.net import AccountClient
from starknet_py.net.account.compiled_account_contract import COMPILED_ACCOUNT_CONTRACT
from starknet_py.tests.e2e.fixtures.constants import (
    CONTRACTS_DIR,
    MAX_FEE,
)
from starknet_py.tests.e2e.fixtures.misc import read_contract


@pytest.fixture(
    scope="module", params=["deploy_map_contract", "new_deploy_map_contract"]
)
def map_contract(request) -> Contract:
    """
    Returns account contracts using old and new account versions
    """
    return request.getfixturevalue(request.param)


@pytest.fixture(scope="module")
def map_source_code() -> str:
    """
    Returns source code of the map contract
    """
    return read_contract("map.cairo", directory=CONTRACTS_DIR)


@pytest.fixture(scope="module")
def map_compiled_contract() -> str:
    """
    Returns compiled map contract
    """
    return read_contract("map_compiled.json")


@pytest.fixture(scope="module")
def erc20_compiled_contract() -> str:
    """
    Returns compiled erc20 contract
    """
    return read_contract("erc20_compiled.json")


@pytest.fixture(scope="module")
def base_compiled_contract() -> str:
    """
    Returns compiled base contract
    """
    return read_contract("base_compiled.json")


@pytest.fixture(scope="module")
def constructor_with_arguments_compiled_contract() -> str:
    """
    Returns compiled constructor_with_arguments contract
    """
    return read_contract("constructor_with_arguments_compiled.json")


@pytest.fixture(scope="module")
def constructor_without_arguments_compiled_contract() -> str:
    """
    Returns compiled constructor_without_arguments contract
    """
    return read_contract("constructor_without_arguments_compiled.json")


async def deploy_contract(
    account_client: AccountClient, class_hash: int, abi: List
) -> Contract:
    """
    Deploys a contract and returns its instance
    """
    deployment_result = await Contract.deploy_contract(
        account=account_client, class_hash=class_hash, abi=abi, max_fee=MAX_FEE
    )
    deployment_result = await deployment_result.wait_for_acceptance()
    return deployment_result.deployed_contract


@pytest_asyncio.fixture(scope="module")
async def deploy_map_contract(
    gateway_account_client: AccountClient,
    map_compiled_contract: str,
    map_class_hash: int,
) -> Contract:
    """
    Deploys map contract and returns its instance
    """
    abi = create_contract_class(compiled_contract=map_compiled_contract).abi
    return await deploy_contract(gateway_account_client, map_class_hash, abi)


@pytest_asyncio.fixture(scope="module")
async def new_deploy_map_contract(
    new_gateway_account_client: AccountClient,
    map_compiled_contract: str,
    map_class_hash: int,
) -> Contract:
    """
    Deploys new map contract and returns its instance
    """
    abi = create_contract_class(compiled_contract=map_compiled_contract).abi
    return await deploy_contract(new_gateway_account_client, map_class_hash, abi)


@pytest_asyncio.fixture(name="erc20_contract", scope="module")
async def deploy_erc20_contract(
    gateway_account_client: AccountClient,
    erc20_compiled_contract: str,
    erc20_class_hash: int,
) -> Contract:
    """
    Deploys erc20 contract and returns its instance
    """
    abi = create_contract_class(compiled_contract=erc20_compiled_contract).abi
    return await deploy_contract(gateway_account_client, erc20_class_hash, abi)


@pytest.fixture(scope="module")
def fee_contract(new_gateway_account_client: AccountClient) -> Contract:
    """
    Returns an instance of the fee contract. It is used to transfer tokens
    """
    abi = [
        {
            "inputs": [
                {"name": "recipient", "type": "felt"},
                {"name": "amount", "type": "Uint256"},
            ],
            "name": "transfer",
            "outputs": [{"name": "success", "type": "felt"}],
            "type": "function",
        },
        {
            "members": [
                {"name": "low", "offset": 0, "type": "felt"},
                {"name": "high", "offset": 1, "type": "felt"},
            ],
            "name": "Uint256",
            "size": 2,
            "type": "struct",
        },
    ]

    return Contract(
        address=FEE_CONTRACT_ADDRESS,
        abi=abi,
        client=new_gateway_account_client,
    )


@pytest.fixture(name="balance_contract")
def fixture_balance_contract() -> str:
    """
    Returns compiled code of the balance.cairo contract
    """
    return read_contract("balance_compiled.json")


async def declare_account(
    account: AccountClient, compiled_account_contract: str
) -> int:
    """
    Declares a specified account
    """

    declare_tx = await account.sign_declare_transaction(
        compiled_contract=compiled_account_contract,
        max_fee=MAX_FEE,
    )
    resp = await account.declare(transaction=declare_tx)
    await account.wait_for_tx(resp.transaction_hash)

    return resp.class_hash


@pytest_asyncio.fixture(scope="module")
async def account_with_validate_deploy_class_hash(
    pre_deployed_account_with_validate_deploy: AccountClient,
) -> int:
    compiled_contract = read_contract("account_with_validate_deploy_compiled.json")
    return await declare_account(
        pre_deployed_account_with_validate_deploy, compiled_contract
    )


@pytest_asyncio.fixture(scope="module")
async def account_without_validate_deploy_class_hash(
    pre_deployed_account_with_validate_deploy: AccountClient,
) -> int:
    return await declare_account(
        pre_deployed_account_with_validate_deploy, COMPILED_ACCOUNT_CONTRACT
    )


@pytest_asyncio.fixture(scope="module")
async def map_class_hash(
    new_gateway_account_client: AccountClient, map_source_code: str
) -> int:
    """
    Returns class_hash of the map.cairo
    """
    declare = await new_gateway_account_client.sign_declare_transaction(
        compilation_source=map_source_code,
        max_fee=int(1e16),
    )
    res = await new_gateway_account_client.declare(declare)
    await new_gateway_account_client.wait_for_tx(res.transaction_hash)
    return res.class_hash


@pytest_asyncio.fixture(scope="module")
async def erc20_class_hash(
    new_gateway_account_client: AccountClient, erc20_compiled_contract: str
) -> int:
    """
    Returns class_hash of the erc20.cairo
    """
    declare = await new_gateway_account_client.sign_declare_transaction(
        compiled_contract=erc20_compiled_contract,
        max_fee=int(1e16),
    )
    res = await new_gateway_account_client.declare(declare)
    await new_gateway_account_client.wait_for_tx(res.transaction_hash)
    return res.class_hash


constructor_with_arguments_source = (
    CONTRACTS_DIR / "constructor_with_arguments.cairo"
).read_text("utf-8")


@pytest.fixture(scope="module")
def constructor_with_arguments_abi() -> List:
    """
    Returns an abi of the constructor_with_arguments.cairo
    """
    compiled_contract = create_compiled_contract(
        compilation_source=constructor_with_arguments_source
    )
    return compiled_contract.abi


@pytest_asyncio.fixture(scope="module")
async def constructor_with_arguments_class_hash(
    new_gateway_account_client: AccountClient,
) -> int:
    """
    Returns a class_hash of the constructor_with_arguments.cairo
    """
    declare = await new_gateway_account_client.sign_declare_transaction(
        compilation_source=constructor_with_arguments_source,
        max_fee=int(1e16),
    )
    res = await new_gateway_account_client.declare(declare)
    await new_gateway_account_client.wait_for_tx(res.transaction_hash)
    return res.class_hash
