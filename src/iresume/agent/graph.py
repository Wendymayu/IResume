import logging

from langgraph.graph import END, StateGraph

from iresume.agent.nodes import (
    gap_analyzer,
    jd_parser,
    markdown_exporter,
    profile_loader,
    resume_generator,
    skill_matcher,
)
from iresume.agent.state import ResumeState

logger = logging.getLogger(__name__)


def _decide_after_gap_analysis(state: ResumeState) -> str:
    gap_report = state.get("gap_report")
    if not gap_report:
        logger.warning("[graph] gap_report 为空，默认返回 proceed")
        return "proceed"
    recommendation = gap_report.get("recommendation", "proceed")
    logger.info(f"[graph] 缺口分析决策: {recommendation}")
    return recommendation


def build_resume_graph() -> StateGraph:
    logger.info("[graph] 开始构建简历生成图")
    graph = StateGraph(ResumeState)

    # Nodes
    graph.add_node("start", lambda state: state)
    graph.add_node("jd_parser", jd_parser.run)
    graph.add_node("profile_loader", profile_loader.run)
    graph.add_node("skill_matcher", skill_matcher.run)
    graph.add_node("gap_analyzer", gap_analyzer.run)
    graph.add_node("resume_generator", resume_generator.run)
    graph.add_node("markdown_exporter", markdown_exporter.run)

    # Entry
    graph.set_entry_point("start")

    # Fan-out: start → jd_parser and profile_loader in parallel
    graph.add_edge("start", "jd_parser")
    graph.add_edge("start", "profile_loader")

    # Fan-in: both → skill_matcher
    graph.add_edge("jd_parser", "skill_matcher")
    graph.add_edge("profile_loader", "skill_matcher")

    # Sequential: skill_matcher → gap_analyzer
    graph.add_edge("skill_matcher", "gap_analyzer")

    # Conditional: gap_analyzer decides whether to proceed
    graph.add_conditional_edges(
        "gap_analyzer",
        _decide_after_gap_analysis,
        {
            "proceed": "resume_generator",
            "proceed_with_caveats": "resume_generator",
            "not_viable": END,
        },
    )

    # Final pipeline
    graph.add_edge("resume_generator", "markdown_exporter")
    graph.add_edge("markdown_exporter", END)

    compiled_graph = graph.compile()
    logger.info("[graph] 图构建完成")
    return compiled_graph
