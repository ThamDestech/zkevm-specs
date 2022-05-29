import pytest

from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    Block,
    Bytecode,
    RWDictionary,
)
from zkevm_specs.util import (
    rand_fq,
    rand_range,
    rand_word,
    RLC,
    U256,
)


TESTING_MAX_RLC = (1 << 256) - 1

TESTING_DATA = (
    (0xABCD << 240, 8),
    (0x1234 << 240, 7),
    (0x8765 << 240, 17),
    (0x4321 << 240, 0),
    (0xFFFF, 256),
    (0x12345, 256 + 8 + 1),
    (TESTING_MAX_RLC, 63),
    (TESTING_MAX_RLC, 128),
    (TESTING_MAX_RLC, 129),
)


@pytest.mark.parametrize("value, shift", TESTING_DATA)
def test_shl(value: U256, shift: int):
    result = value << shift & TESTING_MAX_RLC if shift <= 255 else 0

    randomness = rand_fq()
    value = RLC(value, randomness)
    shift = RLC(shift, randomness)
    result = RLC(result, randomness)

    bytecode = Bytecode().push32(value).push32(shift).shl().stop()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(
            RWDictionary(9)
            .stack_read(1, 1022, value)
            .stack_read(1, 1023, shift)
            .stack_write(1, 1023, result)
            .rws
        ),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.SHL,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=66,
                stack_pointer=1022,
                gas_left=3,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=11,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=67,
                stack_pointer=1023,
                gas_left=0,
            ),
        ],
    )
