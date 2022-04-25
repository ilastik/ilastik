import nifty
import numpy

LEGACY_SOLVER_NAMES = [
    "Nifty_ExactCplex",
    "Nifty_ExactGurobi",
    "Nifty_FmCplex",
    "Nifty_FmGreedy",
    "Nifty_FmGurobi",
    "Opengm_Cgc",
    "Opengm_Exact",
    "Opengm_IntersectionBased",
]


def legacy_nifty_fm_greedy_solver(graph, edge_weights) -> numpy.ndarray:
    """legacy multicut solver method

    replicates pre 1.4.0 behavior. This solver is non-deterministic
    """
    obj = nifty.graph.multicut.multicutObjective(graph, edge_weights)
    greedy = obj.greedyAdditiveFactory().create(obj)
    inf = obj.ccFusionMoveBasedFactory(
        fusionMove=obj.fusionMoveSettings(mcFactory=obj.greedyAdditiveFactory()),
        proposalGenerator=obj.watershedCcProposals(sigma=1, numberOfSeeds=0.01),
        numberOfIterations=500,
        numberOfThreads=8,
        stopIfNoImprovement=20,
    ).create(obj)

    ret = greedy.optimize()
    assert ret is not None
    ret = inf.optimize(visitor=obj.verboseVisitor(), nodeLabels=ret)
    return ret
