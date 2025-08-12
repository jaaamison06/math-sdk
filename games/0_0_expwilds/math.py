"""Lightweight math entrypoint for this slot.

Exports:
- spin(mode: str = "base", seed: Optional[int] = None, criteria: Optional[str] = None) -> dict
  Runs a single simulated round and returns the JSON-ready result dict.
- run(num_sims: int = 100, mode: str = "base", threads: int = 1, batch_size: int = 50000, compression: bool = True, profiling: bool = False) -> None
  Generates full math outputs (books, lookup tables, index/configs) to this slot's library directory.
"""

from typing import Optional, Dict, Any, List
import random

from gamestate import GameState
from game_config import GameConfig
from src.state.run_sims import create_books
from src.write_data.write_configs import generate_configs


def available_modes() -> List[str]:
    cfg = GameConfig()
    return [bm.get_name() for bm in cfg.bet_modes]


def _choose_criteria_for_mode(gamestate: GameState, mode: str) -> str:
    betmode = gamestate.get_betmode(mode)
    distributions = betmode.get_distributions()
    criteria_names = [d._criteria for d in distributions]
    weights = [d._quota for d in distributions]
    return random.choices(criteria_names, weights=weights)[0]


def spin(mode: str = "base", seed: Optional[int] = None, criteria: Optional[str] = None) -> Dict[str, Any]:
    """Simulate a single round and return the result dict."""
    config = GameConfig()
    gamestate = GameState(config)

    modes = [bm.get_name() for bm in config.bet_modes]
    if mode not in modes:
        raise ValueError(f"Unknown mode '{mode}'. Valid modes: {modes}")

    gamestate.betmode = mode
    if criteria is None:
        criteria = _choose_criteria_for_mode(gamestate, mode)
    # basic validation when caller passes a criteria explicitly
    valid_criteria = [d._criteria for d in gamestate.get_betmode(mode).get_distributions()]
    if criteria not in valid_criteria:
        raise ValueError(f"Unknown criteria '{criteria}' for mode '{mode}'. Valid criteria: {valid_criteria}")

    gamestate.criteria = criteria

    if seed is None:
        seed = random.randint(0, 2**31 - 1)

    gamestate.run_spin(seed)
    # library contains a single entry keyed by seed+1
    return next(iter(gamestate.library.values()))


def run(
    num_sims: int = 100,
    mode: str = "base",
    threads: int = 1,
    batch_size: int = 50000,
    compression: bool = True,
    profiling: bool = False,
) -> None:
    """Generate math outputs (books, LUTs, configs) for this slot.

    Files are written under this slot's `library/` directory.
    """
    config = GameConfig()
    gamestate = GameState(config)

    num_sim_args = {mode: int(num_sims)}

    create_books(
        gamestate=gamestate,
        config=config,
        num_sim_args=num_sim_args,
        batch_size=batch_size,
        threads=threads,
        compress=compression,
        profiling=profiling,
    )

    generate_configs(gamestate)