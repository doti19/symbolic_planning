import { fitScene, spriteGeometry } from "./vfg.mjs";

export async function loadTextures(scene) {
  const used = new Set(scene.stages.flatMap(stage => stage.sprites.map(sprite => sprite.prefabimage)));
  const textures = await Promise.all([...used].map(async key => {
    const image = new Image();
    image.src = `data:image/png;base64,${scene.images.get(key)}`;
    await image.decode();
    return [key, image];
  }));
  return new Map(textures);
}

const tints = new WeakMap();

function tinted(image, color) {
  const channels = ["r", "g", "b"].map(channel => {
    const value = color?.[channel];
    return Number.isFinite(value) ? Math.round(Math.max(0, Math.min(1, value)) * 255) : 255;
  });
  if (channels.every(value => value === 255)) return image;
  if (!tints.has(image)) tints.set(image, new Map());
  const cache = tints.get(image);
  const key = channels.join(",");
  if (!cache.has(key)) {
    const canvas = document.createElement("canvas");
    canvas.width = image.naturalWidth;
    canvas.height = image.naturalHeight;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = `rgb(${key})`;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.globalCompositeOperation = "multiply";
    ctx.drawImage(image, 0, 0);
    ctx.globalCompositeOperation = "destination-in";
    ctx.drawImage(image, 0, 0);
    cache.set(key, canvas);
  }
  return cache.get(key);
}

export function drawScene(ctx, scene, textures, sprites, width, height, padding) {
  if (width <= 2 * padding || height <= 2 * padding) return;
  const { bounds } = scene;
  const view = fitScene(bounds, width, height, padding);

  ctx.fillStyle = "#f8fafc";
  ctx.fillRect(view.left - 7, view.top - 7, view.width + 14, view.height + 14);
  ctx.imageSmoothingQuality = "high";
  for (const sprite of sprites) {
    const geom = spriteGeometry(sprite);
    if (!geom.width || !geom.height || sprite.color?.a === 0) continue;
    const x = view.left + (geom.x - bounds.left) * view.scale;
    const y = view.top + (geom.y - bounds.top) * view.scale;
    const w = geom.width * view.scale;
    const h = geom.height * view.scale;

    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(geom.angle);
    ctx.globalAlpha = sprite.color?.a ?? 1;
    ctx.drawImage(tinted(textures.get(sprite.prefabimage), sprite.color), -w / 2, -h / 2, w, h);
    ctx.restore();

    ctx.font = '600 15px "DM Sans", sans-serif';
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    if (sprite.showlabel === true && typeof sprite.label === "string") {
      ctx.fillStyle = "#a64826";
      ctx.fillText(sprite.label, x, y);
    }
    if (sprite.showname === true) {
      ctx.fillStyle = "#142d43";
      ctx.fillText(sprite.name, x, sprite.showlabel === true ? y - h / 2 - 9 : y);
    }
  }
}
