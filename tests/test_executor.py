import subprocess
from pathlib import Path
from unittest import mock
from executor.verefoo_runner import run_single_verefoo, run_verefoo_parallel


@mock.patch("executor.verefoo_runner.VEREFOO_COMMAND", [
    "echo", "200"
])
def test_run_single_verefoo_success(tmp_path):
    input_path = tmp_path / "test_input.xml"
    output_path = tmp_path / "test_input_output.xml"

    input_path.write_text("""
    <root>
        <content>test</content>
    </root>
    """)

    output_path.write_text("""
    <simulation>
        <result>success</result>
    </simulation>
    """)

    with mock.patch("executor.verefoo_runner.VEREFOO_OUTPUT_DIR", tmp_path):
        result = run_single_verefoo(str(input_path))
        assert result == str(output_path)
        assert output_path.exists()


@mock.patch("executor.verefoo_runner.VEREFOO_COMMAND", ["echo", "500"])
def test_run_single_verefoo_failure_code(tmp_path):
    input_path = tmp_path / "fail_input.xml"
    output_path = tmp_path / "fail_input_output.xml"
    input_path.write_text("<invalid></invalid>")
    output_path.write_text("<message>Error occurred</message>")

    with mock.patch("executor.verefoo_runner.VEREFOO_OUTPUT_DIR", tmp_path):
        result = run_single_verefoo(str(input_path))
        assert result is None


@mock.patch("executor.verefoo_runner.subprocess.run")
def test_run_single_verefoo_timeout(mock_run, tmp_path):
    input_path = tmp_path / "timeout_input.xml"
    input_path.write_text("<xml></xml>")

    mock_run.side_effect = subprocess.TimeoutExpired(cmd="verefoo", timeout=5)

    with mock.patch("executor.verefoo_runner.VEREFOO_OUTPUT_DIR", tmp_path):
        result = run_single_verefoo(str(input_path))
        assert result.endswith("_output.xml")
        assert not Path(result).exists()


@mock.patch("executor.verefoo_runner.subprocess.run")
def test_run_single_verefoo_crash(mock_run, tmp_path):
    input_path = tmp_path / "crash_input.xml"
    input_path.write_text("<xml></xml>")

    mock_run.side_effect = subprocess.CalledProcessError(1, "verefoo")

    with mock.patch("executor.verefoo_runner.VEREFOO_OUTPUT_DIR", tmp_path):
        result = run_single_verefoo(str(input_path))
        assert result.endswith("_output.xml")
        assert not Path(result).exists()


def test_run_verefoo_parallel_mocked_pool(tmp_path):
    inputs = [tmp_path / f"area{i}.xml" for i in range(2)]
    for f in inputs:
        f.write_text("<root></root>")

    expected_outputs = [str(f).replace(".xml", "_output.xml") for f in inputs]

    with mock.patch("executor.verefoo_runner.run_single_verefoo") as mock_run:
        mock_run.side_effect = expected_outputs
        with mock.patch("executor.verefoo_runner.Pool") as mock_pool:
            mock_pool.return_value.__enter__.return_value.map.side_effect = lambda func, paths: list(
                map(mock_run, paths))
            results = run_verefoo_parallel([str(f) for f in inputs])
            assert results == expected_outputs
            assert mock_run.call_count == 2


def test_run_single_verefoo_missing_output(tmp_path):
    input_path = tmp_path / "missing_output.xml"
    input_path.write_text("<root><child/></root>")

    with mock.patch("executor.verefoo_runner.VEREFOO_OUTPUT_DIR", tmp_path):
        with mock.patch("executor.verefoo_runner.VEREFOO_COMMAND", ["echo", "200"]):
            # Create mock that does NOT write the output file
            with mock.patch("executor.verefoo_runner.subprocess.run") as mock_run:
                mock_run.return_value.stdout = "200"
                result = run_single_verefoo(str(input_path))
                assert result is None


def test_run_single_verefoo_malformed_error_output(tmp_path):
    input_path = tmp_path / "malformed_input.xml"
    output_path = tmp_path / "malformed_input_output.xml"
    input_path.write_text("<invalid></invalid>")
    output_path.write_text("not_xml")

    with mock.patch("executor.verefoo_runner.VEREFOO_OUTPUT_DIR", tmp_path):
        with mock.patch("executor.verefoo_runner.VEREFOO_COMMAND", ["echo", "500"]):
            result = run_single_verefoo(str(input_path))
            assert result is None
