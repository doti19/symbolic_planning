import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";
import { fitScene, goalStatus, parseVfg, sampleFrame, stepMs } from "./vfg.mjs";

async function demo(name) {
  const url = new URL(`demos/${name}.vfg`, import.meta.url);
  return parseVfg(await readFile(url, "utf8"));
}

function sprite(frame, name) {
  const match = frame.sprites.find(sprite => sprite.name === name);
  assert.ok(match, name);
  return match;
}

test("carried items keep their gripper offsets through the room transition", async () => {
  const scene = await demo("two-object-transport");
  const before = sampleFrame(scene, 4 * stepMs);
  const moving = sampleFrame(scene, 5 * stepMs - 350);
  const after = sampleFrame(scene, 5 * stepMs);
  const start = sprite(before, "robot");
  const transit = sprite(moving, "robot");
  const end = sprite(after, "robot");

  assert.equal(moving.index, 4);
  assert.equal(transit.minY, (start.minY + end.minY) / 2);
  for (const name of ["book", "laptop"]) {
    const held = sprite(moving, name);
    assert.equal(held.minX - transit.minX, sprite(before, name).minX - start.minX);
    assert.ok(Math.abs((held.minY - transit.minY) - (sprite(before, name).minY - start.minY)) < .001);
  }

  const placed = sampleFrame(scene, 7 * stepMs);
  assert.ok(sprite(placed, "book").maxX < sprite(placed, "laptop").minX);
  assert.equal(goalStatus(scene, 6).label, "Goal 1 / 2");
  assert.equal(goalStatus(scene, 7).label, "Goal reached");
});

test("the cabinet texture changes on the VFG state boundary", async () => {
  const scene = await demo("cabinet-retrieval");
  const before = sampleFrame(scene, 3 * stepMs - 1);
  const open = sampleFrame(scene, 3 * stepMs);
  assert.equal(sprite(before, "office-cabinet").prefabimage, "img-cabinet-closed");
  assert.equal(sprite(open, "office-cabinet").prefabimage, "img-cabinet-open");
  assert.ok(sprite(open, "office-cabinet").depth > sprite(open, "book").depth);
});

test("the scene fits and centers uniformly on a wide or tall canvas", async () => {
  const { bounds } = await demo("cabinet-retrieval");
  for (const [width, height] of [[1120, 894], [746, 582], [400, 700]]) {
    const layout = fitScene(bounds, width, height, 26);
    assert.ok(Math.abs(layout.width - layout.height) < 1e-9);
    assert.ok(Math.abs(layout.width - (Math.min(width, height) - 52)) < 1e-9);
    assert.ok(Math.abs(layout.left * 2 + layout.width - width) < 1e-9);
    assert.ok(Math.abs(layout.top * 2 + layout.height - height) < 1e-9);
  }
});

test("invalid and empty VFG files provide readable errors", () => {
  assert.throws(() => parseVfg("{"), /not valid JSON/);
  assert.throws(() => parseVfg('{"visualStages":[]}'), /no animation stages/);
});
