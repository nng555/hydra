# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
from textwrap import dedent

import subprocess
import sys
from difflib import unified_diff
from pathlib import Path
from typing import Any

import pytest
from omegaconf import OmegaConf

from configen.config import ConfigenConf, ModuleConf
from configen.configen import generate_module
from hydra.test_utils.test_utils import chdir_hydra_root, get_run_output

chdir_hydra_root(subdir="tools/configen")

##
# To re-generate the expected config run the following command from configen's root directory (tools/configen).
#
# PYTHONPATH=. configen --config-dir tests/gen-test-expected/
#
##
conf: ConfigenConf = OmegaConf.structured(
    ConfigenConf(
        header="""# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
# Generated by configen, do not edit.
# See https://github.com/facebookresearch/hydra/tree/master/tools/configen
# fmt: off
# isort:skip_file
# flake8: noqa
"""
    )
)


@pytest.mark.parametrize(
    "class_name",
    [
        "Empty",
        "UntypedArg",
        "IntArg",
        "UnionArg",
        "WithLibraryClassArg",
        "IncompatibleDataclassArg",
        "WithStringDefault",
        "ListValues",
        "DictValues",
        "PeskySentinelUsage",
    ],
)
def test_generated_code(class_name: str) -> None:
    module_name = "tests.test_modules"
    expected_file = (
        Path(module_name.replace(".", "/")) / "expected" / f"{class_name}.py"
    )
    expected = expected_file.read_text()

    generated = generate_module(
        cfg=conf,
        module=ModuleConf(
            name=module_name,
            classes=[class_name],
        ),
    )

    lines = [
        line
        for line in unified_diff(
            expected.splitlines(),
            generated.splitlines(),
            fromfile=str(expected_file),
            tofile="Generated",
        )
    ]

    diff = "\n".join(lines)
    if generated != expected:
        print(diff)
        assert False, f"Mismatch between {expected_file} and generated code"


def test_example_application(monkeypatch: Any, tmpdir: Path):
    monkeypatch.chdir("example")
    cmd = [
        "my_app.py",
        f"hydra.run.dir={tmpdir}",
        "user.name=Batman",
    ]
    result, _err = get_run_output(cmd)
    assert result == dedent(
        """\
    User: name=Batman, age=7
    Admin: name=Lex Luthor, age=10, private_key=deadbeef"""
    )
