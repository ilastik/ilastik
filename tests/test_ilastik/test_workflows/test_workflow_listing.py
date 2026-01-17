from unittest.mock import Mock

import pytest

import ilastik.workflow
import ilastik.workflows


@pytest.mark.parametrize(
    "workflow_subclasses,expected",
    [
        ([Mock(workflowName="Test", __name__="Test", workflowDisplayName=None)], (("Test", "Test"),)),
        ([Mock(workflowName=None, __name__="TestWorkflow", workflowDisplayName=None)], (("Test", "Test"),)),
        (
            [Mock(workflowName="Test", __name__="Test", workflowDisplayName="TestDisplay")],
            (("Test", "TestDisplay"),),
        ),
        (
            [
                Mock(workflowName="1", __name__="1", workflowDisplayName=None),
                Mock(workflowName="2", __name__="2", workflowDisplayName="2Disp"),
            ],
            (
                ("1", "1"),
                ("2", "2Disp"),
            ),
        ),
        ([Mock(workflowName="Test", __name__="Test", workflowDisplayName=None)], (("Test", "Test"),)),
        ([Mock(workflowName="TestBase", __name__="Test", workflowDisplayName=None)], tuple()),
        (
            [
                Mock(workflowName="Test", __name__="Test", workflowDisplayName=None),
                Mock(workflowName="Test", __name__="Test", workflowDisplayName=None),
            ],
            (("Test", "Test"),),
        ),
    ],
)
def test_listing(monkeypatch, workflow_subclasses, expected):
    monkeypatch.setattr(ilastik.workflow, "all_subclasses", lambda _: workflow_subclasses)
    discovered_workflows = list(ilastik.workflow.getAvailableWorkflows())

    assert len(discovered_workflows) == len(expected)
    for disc, exp in zip(discovered_workflows, expected):
        assert disc[1] == exp[0]
        assert disc[2] == exp[1]
