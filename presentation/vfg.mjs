// Positions use the VFG's normalized, bottom-left coordinate system.
const coordinates = ["minX", "minY", "maxX", "maxY"];
const holdMs = 900;
const transitionMs = 700;
export const stepMs = holdMs + transitionMs;
const finalHoldMs = 1600;

function tableEntries(table) {
  if (!Array.isArray(table?.m_keys) || !Array.isArray(table.m_values)) return [];
  return table.m_keys.map((key, index) => [key, table.m_values[index]]);
}

export function parseVfg(text) {
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error("This file is not valid JSON.");
  }
  if (!Array.isArray(data?.visualStages) || !data.visualStages.length) {
    throw new Error("The VFG has no animation stages.");
  }

  const images = new Map(tableEntries(data.imageTable));
  const stages = data.visualStages.map((stage, index) => {
    if (!Array.isArray(stage?.visualSprites)) {
      throw new Error(`Step ${index} has no sprite list.`);
    }
    const sprites = [...stage.visualSprites];
    const byName = new Map();
    for (const sprite of sprites) {
      if (typeof sprite?.name !== "string" || byName.has(sprite.name) ||
          !coordinates.every(key => Number.isFinite(sprite[key])) ||
          sprite.maxX < sprite.minX || sprite.maxY < sprite.minY) {
        throw new Error(`Step ${index} has invalid sprite names or bounds.`);
      }
      const png = images.get(sprite.prefabimage);
      if (typeof png !== "string" || !png.startsWith("iVBORw0KGgo")) {
        throw new Error(`The sprite "${sprite.name}" has no embedded PNG.`);
      }
      byName.set(sprite.name, sprite);
    }
    sprites.sort((a, b) => (a.depth ?? 0) - (b.depth ?? 0));
    return {
      sprites,
      byName,
      label: typeof stage.stageName === "string" ? stage.stageName : `Step ${index}`,
      final: stage.isFinal === true || stage.isFinal === "true",
    };
  });

  const goals = new Set(tableEntries(data.subgoalPool).map(([key]) => key)
    .filter(key => typeof key === "string"));
  const achieved = new Map();
  for (const [key, values] of tableEntries(data.subgoalMap)) {
    if (!Array.isArray(values)) continue;
    const entries = values.filter(goal => typeof goal === "string");
    for (const goal of entries) goals.add(goal);
    achieved.set(Number(key), new Set(entries));
  }

  return { images, stages, goals: [...goals], achieved, bounds: sceneBounds(stages) };
}

export function spriteGeometry(sprite) {
  const width = sprite.maxX - sprite.minX;
  const height = sprite.maxY - sprite.minY;
  const x = sprite.minX + width / 2;
  const rotated = Number.isFinite(sprite.rotate);
  // Planimation's rotated sprites use the center of the bottom edge as the pivot.
  const y = rotated ? -sprite.minY : -sprite.maxY + height / 2;
  const angle = rotated ? sprite.rotate * Math.PI / 180 : 0;
  return { x, y, width, height, angle };
}

function sceneBounds(stages) {
  const bounds = { left: Infinity, top: Infinity, right: -Infinity, bottom: -Infinity };
  for (const { sprites } of stages) {
    for (const sprite of sprites) {
      const { x, y, width, height, angle } = spriteGeometry(sprite);
      if (!width || !height || sprite.color?.a === 0) continue;
      const cos = Math.abs(Math.cos(angle));
      const sin = Math.abs(Math.sin(angle));
      const dx = (width * cos + height * sin) / 2;
      const dy = (width * sin + height * cos) / 2;
      bounds.left = Math.min(bounds.left, x - dx);
      bounds.top = Math.min(bounds.top, y - dy);
      bounds.right = Math.max(bounds.right, x + dx);
      bounds.bottom = Math.max(bounds.bottom, y + dy);
    }
  }
  if (!Number.isFinite(bounds.left)) throw new Error("The VFG has no visible sprite bounds.");
  return bounds;
}

export function fitScene(bounds, width, height, padding) {
  const sceneWidth = bounds.right - bounds.left;
  const sceneHeight = bounds.bottom - bounds.top;
  const scale = Math.min((width - 2 * padding) / sceneWidth, (height - 2 * padding) / sceneHeight);
  const left = (width - sceneWidth * scale) / 2;
  const top = (height - sceneHeight * scale) / 2;
  return { scale, left, top, width: sceneWidth * scale, height: sceneHeight * scale };
}

export function duration(scene) {
  return (scene.stages.length - 1) * stepMs + finalHoldMs;
}

export function sampleFrame(scene, time) {
  const index = Math.min(Math.floor(Math.max(0, time) / stepMs), scene.stages.length - 1);
  const from = scene.stages[index];
  const to = scene.stages[index + 1];
  const progress = (time - index * stepMs - holdMs) / transitionMs;
  if (!to || progress <= 0) return { index, sprites: from.sprites };
  return {
    index,
    sprites: from.sprites.map(sprite => {
      const end = to.byName.get(sprite.name);
      if (!end || coordinates.every(key => sprite[key] === end[key])) return sprite;
      const tween = { ...sprite };
      for (const key of coordinates) tween[key] += (end[key] - sprite[key]) * progress;
      return tween;
    }),
  };
}

export function goalStatus(scene, index) {
  const achieved = scene.achieved.get(index) ?? new Set();
  const count = scene.goals.filter(goal => achieved.has(goal)).length;
  const reached = count > 0 && count === scene.goals.length;
  let label = "Goal unavailable";
  if (reached) label = "Goal reached";
  else if (scene.goals.length) label = `Goal ${count} / ${scene.goals.length}`;
  else if (scene.stages[index].final) label = "Final frame";
  return { achieved, reached, label };
}

const capitalize = value => value.charAt(0).toUpperCase() + value.slice(1);
const words = value => (value ?? "").replaceAll("-", " ");

export function actionLabel(label) {
  const action = label.match(/^\(([^()]*)\)$/);
  if (!action) return label;
  const [name, a, b] = action[1].trim().split(/\s+/);
  switch (name) {
    case "move": return `Move to ${capitalize(words(b))}`;
    case "pick-up": return `Pick up ${words(a)}`;
    case "open-cabinet": return `Open ${words(a)}`;
    case "open-door": return `Open ${words(a)}`;
    case "take-from-cabinet": return `Retrieve ${words(a)}`;
    case "put-on-table": return `Put ${words(a)} on ${words(b)}`;
    case "hand-over": return `Hand ${words(a)} to ${words(b)}`;
    default: return label;
  }
}

export function goalLabel(label) {
  const goal = label.match(/^\(([^()]*)\)$/);
  if (!goal) return label;
  const [name, a, b] = goal[1].trim().split(/\s+/);
  switch (name) {
    case "on-table": return `${capitalize(words(a))} on ${words(b)}`;
    case "delivered-to": return `${capitalize(words(a))} with ${words(b)}`;
    case "robot-at": return `Robot in ${capitalize(words(a))}`;
    default: return label;
  }
}
