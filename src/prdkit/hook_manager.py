import json
import os
import sys

STATE_FILE = ".memory/workflow_state.json"
MEMORY_DIR = ".memory"

VALID_STAGES = ("init", "clarify", "create", "modify")

VALID_TRANSITS = (
    "init_completed",
    "clarify_completed",
    "re_clarify",
    "direct_modify",
    "completed_create_or_modify",
)


def require_project_root(*, allow_missing_memory: bool = False) -> None:
    """Hook 须在用户项目根目录执行（含 .memory/），首次 init 完成前除外。"""
    if allow_missing_memory or os.path.isdir(MEMORY_DIR):
        return
    print(
        f"❌ [Hook 拦截] 当前目录不是项目根：未找到 {MEMORY_DIR}/。\n"
        f"   请在包含 PRD 工作区的项目根目录执行（pwd: {os.getcwd()}）。"
    )
    sys.exit(1)


def load_state():
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE) or ".", exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def check_hook(requested_stage):
    if requested_stage not in VALID_STAGES:
        print(f"❌ [Hook 拦截] 未知阶段: {requested_stage}。允许值: {', '.join(VALID_STAGES)}")
        sys.exit(1)

    state = load_state()

    if requested_stage == "init":
        require_project_root(allow_missing_memory=state is None)
        if state is None:
            print("✅ [Hook 放行] 允许执行 init 阶段任务（尚未初始化 .memory）。")
            sys.exit(0)
        init_status = state.get("stages", {}).get("init")
        if init_status == "completed":
            print(
                "🛑 [Hook 拦截] init 已完成。请勿重复初始化；请使用 /prd-clarify 或 /prd-create。"
            )
            sys.exit(1)
        if init_status == "locked":
            print("🛑 [Hook 拦截] 当前状态禁止执行 init。")
            sys.exit(1)
        print("✅ [Hook 放行] 允许执行 init 阶段任务。")
        sys.exit(0)

    require_project_root()
    if state is None:
        print("❌ [Hook 拦截] 严重错误：未找到状态文件。请先严格执行 /prd-init！")
        sys.exit(1)

    stages = state.get("stages", {})

    if requested_stage == "clarify":
        if stages.get("init") != "completed":
            print(
                "🛑 [Hook 拦截] 执行中断！必须先完成 /prd-init（stages.init 须为 completed）。"
            )
            sys.exit(1)
        if stages.get("clarify") == "locked":
            print("🛑 [Hook 拦截] 当前状态禁止执行 clarify。")
            sys.exit(1)
        if stages.get("clarify") == "completed" and stages.get("create") != "locked":
            print(
                "🛑 [Hook 拦截] clarify 已完成。请使用 /prd-create 生成 PRD，勿重复澄清。"
            )
            sys.exit(1)
        print("✅ [Hook 放行] 允许执行 clarify 阶段任务。")
        sys.exit(0)

    if requested_stage == "create":
        if stages.get("clarify") != "completed":
            print(
                "🛑 [Hook 拦截] 执行中断！当前状态禁止执行 create。你必须先与用户完成 /prd-clarify！"
            )
            sys.exit(1)
        if stages.get("create") == "locked":
            print(
                "🛑 [Hook 拦截] 当前状态禁止执行 create。请先完成 /prd-clarify（含 modify 倒流后的再澄清）。"
            )
            sys.exit(1)
        print("✅ [Hook 放行] 允许执行 create 阶段任务。")
        sys.exit(0)

    if requested_stage == "modify":
        if stages.get("create") != "completed":
            print(
                "🛑 [Hook 拦截] 执行中断！必须先完成 /prd-create（stages.create 须为 completed）。"
            )
            sys.exit(1)
        modify_status = stages.get("modify")
        if modify_status == "locked":
            print("🛑 [Hook 拦截] 当前状态禁止执行 modify。")
            sys.exit(1)
        if modify_status == "in_progress":
            print("✅ [Hook 放行] 允许执行 modify 阶段任务（direct_modify 轨道）。")
            sys.exit(0)
        if modify_status in ("pending", "completed"):
            print("✅ [Hook 放行] 允许进入 modify 决策流程。")
            sys.exit(0)
        print("🛑 [Hook 拦截] modify 状态异常，请检查 workflow_state.json。")
        sys.exit(1)


def transit(action):
    if action not in VALID_TRANSITS:
        print(f"❌ [Hook 拦截] 未知流转: {action}。允许值: {', '.join(VALID_TRANSITS)}")
        sys.exit(1)

    if action == "init_completed":
        save_state(
            {
                "current_stage": "init",
                "stages": {
                    "init": "completed",
                    "clarify": "pending",
                    "create": "locked",
                    "modify": "locked",
                },
            }
        )
        print(
            "✅ [Hook 流转] init 已完成：clarify=pending，create/modify=locked。请执行 /prd-clarify。"
        )
        sys.exit(0)

    require_project_root()
    state = load_state()
    if state is None:
        print("❌ [Hook 拦截] 严重错误：未找到状态文件。请先严格执行 /prd-init！")
        sys.exit(1)

    stages = state.setdefault("stages", {})

    if action == "clarify_completed":
        stages = state.setdefault("stages", {})
        state["current_stage"] = "clarify"
        stages["init"] = "completed"
        stages["clarify"] = "completed"
        if stages.get("create") == "locked":
            stages["create"] = "pending"
        stages.setdefault("modify", "locked")
        state.pop("modify_track", None)
        save_state(state)
        print("✅ [Hook 流转] clarify 已完成：create=pending。请执行 /prd-create。")
        sys.exit(0)

    if action == "re_clarify":
        if stages.get("create") != "completed":
            print("🛑 [Hook 拦截] 无法倒流：尚未完成首次 /prd-create。")
            sys.exit(1)
        state["current_stage"] = "clarify"
        stages["init"] = "completed"
        stages["clarify"] = "pending"
        stages["create"] = "locked"
        stages["modify"] = "locked"
        state["modify_track"] = "re_clarify"
        save_state(state)
        print(
            "✅ [Hook 流转] 已切换至「重走澄清」轨道：clarify=pending，create=locked。请执行 /prd-clarify。"
        )
        sys.exit(0)

    if action == "direct_modify":
        if stages.get("create") != "completed":
            print("🛑 [Hook 拦截] 无法直接修改：尚未完成 /prd-create。")
            sys.exit(1)
        state["current_stage"] = "modify"
        stages["modify"] = "in_progress"
        state["modify_track"] = "direct_modify"
        save_state(state)
        print("✅ [Hook 流转] 已切换至「直接修改」轨道：modify=in_progress。")
        sys.exit(0)

    if action == "completed_create_or_modify":
        state["current_stage"] = "create"
        stages["init"] = "completed"
        stages["clarify"] = "completed"
        stages["create"] = "completed"
        stages["modify"] = "pending"
        state.pop("modify_track", None)
        save_state(state)
        print(
            "✅ [Hook 流转] 本轮 create/modify 已闭环：create=completed，modify=pending（可再次进入 modify）。"
        )
        sys.exit(0)


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "❌ [Hook 拦截] 缺少参数。\n"
            "用法:\n"
            "  prdkit-hook <init|clarify|create|modify>\n"
            "  prdkit-hook check <init|clarify|create|modify>\n"
            "  prdkit-hook transit <init_completed|clarify_completed|re_clarify|direct_modify|completed_create_or_modify>"
        )
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "check":
        if len(sys.argv) < 3:
            print("❌ [Hook 拦截] check 缺少阶段参数。")
            sys.exit(1)
        check_hook(sys.argv[2].lower())
    elif cmd == "transit":
        if len(sys.argv) < 3:
            print("❌ [Hook 拦截] transit 缺少流转参数。")
            sys.exit(1)
        transit(sys.argv[2].lower())
    else:
        check_hook(cmd)


if __name__ == "__main__":
    main()
