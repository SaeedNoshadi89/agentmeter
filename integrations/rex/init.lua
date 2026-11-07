-- agentmeter: popup with Claude Code / Codex 5h + weekly usage remaining.
-- install.sh fills in the command path and shortcut placeholders below.
rex.action{
  name     = "agent_usage",
  title    = "Show Agent Usage",
  keywords = "claude codex limits quota usage",
  run = function(ctx, args)
    return rex.session.new_layer{
      session_id = ctx.session_id,
      bounds = { 0.34, 0.32, 0.32, 0.22 },
      focus  = true,
      layout = rex.layout.block{
        flavor  = "com.superlogical.terminal.shell",
        options = { command = { "@AGENTMETER_BIN@", "--popup" } },
      },
    }
  end,
}
rex.bind("@AGENTMETER_KEY@", "agent_usage")
