--- 最小化导出：仅写已研究科技 + 已启用配方（可制造物品由工具端从配方库推导）

local exported = false

local function write_error(msg)
  log("[factory-balance-sync] ERROR: " .. msg)
  if helpers and helpers.write_file then
    helpers.write_file("factory-balance-error.txt", msg)
  end
end

local function export_progress()
  if exported then
    return
  end

  local ok, err = pcall(function()
    local force = game.forces["player"]
    if not force then
      error("force 'player' 不存在")
    end

    local researched = {}
    for name, tech in pairs(force.technologies) do
      if tech.researched then
        table.insert(researched, name)
      end
    end
    table.sort(researched)

    local enabled_recipes = {}
    for name, recipe in pairs(force.recipes) do
      if recipe.enabled then
        table.insert(enabled_recipes, name)
      end
    end
    table.sort(enabled_recipes)

    local mod_names = {}
    for name, _ in pairs(script.active_mods) do
      table.insert(mod_names, name)
    end
    table.sort(mod_names)

    local payload = {
      researched_technologies = researched,
      enabled_recipes = enabled_recipes,
      mod_names = mod_names,
      tick = game.tick,
      exported_at_tick = game.tick,
    }

    local json = helpers.table_to_json(payload)
    helpers.write_file("factory-balance-progress.json", json)
    exported = true
    log("[factory-balance-sync] exported " .. #enabled_recipes .. " recipes")
  end)

  if not ok then
    write_error(tostring(err))
    exported = true
  end
end

script.on_nth_tick(1, function()
  export_progress()
end)
