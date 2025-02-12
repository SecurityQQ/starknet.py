import pytest

from starknet_py.contract import Contract
from starknet_py.net.udc_deployer.deployer import Deployer
from starknet_py.tests.e2e.utils import MAX_FEE
from starknet_py.utils.contructor_args_translator import translate_constructor_args


@pytest.mark.asyncio
async def test_default_deploy_with_class_hash(account_client, map_class_hash):
    deployer = Deployer()

    deploy_call, address = deployer.create_deployment_call(class_hash=map_class_hash)

    deploy_invoke_tx = await account_client.sign_invoke_transaction(
        deploy_call, max_fee=MAX_FEE
    )
    resp = await account_client.send_transaction(deploy_invoke_tx)
    await account_client.wait_for_tx(resp.transaction_hash)

    assert isinstance(address, int)
    assert address != 0


@pytest.mark.asyncio
async def test_throws_when_calldata_provided_without_abi(map_class_hash):
    deployer = Deployer()

    with pytest.raises(ValueError) as err:
        deployer.create_deployment_call(class_hash=map_class_hash, calldata=[12, 34])

    assert "calldata was provided without an abi" in str(err.value)


@pytest.mark.asyncio
async def test_throws_when_calldata_not_provided(constructor_with_arguments_abi):
    deployer = Deployer()

    with pytest.raises(ValueError) as err:
        deployer.create_deployment_call(
            class_hash=1234, abi=constructor_with_arguments_abi
        )

    assert "Provided contract has a constructor and no arguments were provided." in str(
        err.value
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "calldata",
    [
        [10, (1, (2, 3)), [1, 2, 3], {"value": 12, "nested_struct": {"value": 99}}],
        {
            "single_value": 10,
            "tuple": (1, (2, 3)),
            "arr": [1, 2, 3],
            "dict": {"value": 12, "nested_struct": {"value": 99}},
        },
    ],
)
async def test_constructor_arguments_contract_deploy(
    account_client,
    constructor_with_arguments_abi,
    constructor_with_arguments_class_hash,
    calldata,
):
    deployer = Deployer(account_address=account_client.address)

    (deploy_call, contract_address,) = deployer.create_deployment_call(
        class_hash=constructor_with_arguments_class_hash,
        abi=constructor_with_arguments_abi,
        calldata=calldata,
    )

    deploy_invoke_transaction = await account_client.sign_invoke_transaction(
        deploy_call, max_fee=MAX_FEE
    )
    resp = await account_client.send_transaction(deploy_invoke_transaction)
    await account_client.wait_for_tx(resp.transaction_hash)

    contract = Contract(
        address=contract_address,
        abi=constructor_with_arguments_abi,
        client=account_client,
    )

    result = await contract.functions["get"].call(block_hash="latest")

    assert result == (
        10,
        (1, (2, 3)),
        sum([1, 2, 3]),
        {"value": 12, "nested_struct": {"value": 99}},
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "salt, pass_account_address", [(1, True), (2, False), (None, True), (None, False)]
)
async def test_address_computation(
    salt, pass_account_address, new_gateway_account_client, map_class_hash
):
    deployer = Deployer(
        account_address=new_gateway_account_client.address
        if pass_account_address
        else None
    )

    deploy_call, computed_address = deployer.create_deployment_call(
        class_hash=map_class_hash, salt=salt
    )

    deploy_invoke_tx = await new_gateway_account_client.sign_invoke_transaction(
        deploy_call, max_fee=MAX_FEE
    )
    resp = await new_gateway_account_client.send_transaction(deploy_invoke_tx)
    await new_gateway_account_client.wait_for_tx(resp.transaction_hash)

    tx_receipt = await new_gateway_account_client.get_transaction_receipt(
        resp.transaction_hash
    )
    address_from_event = tx_receipt.events[0].data[0]

    assert computed_address == address_from_event


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "calldata",
    [
        [10, (1, (2, 3)), [1, 2, 3], {"value": 12, "nested_struct": {"value": 99}}],
        {
            "single_value": 10,
            "tuple": (1, (2, 3)),
            "arr": [1, 2, 3],
            "dict": {"value": 12, "nested_struct": {"value": 99}},
        },
    ],
)
async def test_create_deployment_call_raw(
    account_client,
    constructor_with_arguments_abi,
    constructor_with_arguments_class_hash,
    calldata,
):
    deployer = Deployer(account_address=account_client.address)

    raw_calldata = translate_constructor_args(
        abi=constructor_with_arguments_abi or [], constructor_args=calldata
    )

    (deploy_call, contract_address,) = deployer.create_deployment_call_raw(
        class_hash=constructor_with_arguments_class_hash,
        raw_calldata=raw_calldata,
    )

    deploy_invoke_transaction = await account_client.sign_invoke_transaction(
        deploy_call, max_fee=MAX_FEE
    )
    resp = await account_client.send_transaction(deploy_invoke_transaction)
    await account_client.wait_for_tx(resp.transaction_hash)

    assert isinstance(contract_address, int)
    assert contract_address != 0
