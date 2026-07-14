import assert from "node:assert/strict";
import test from "node:test";

import { slugify } from "../src/slugify.mjs";

test("slugify normalizes words and punctuation", () => {
  assert.equal(slugify(" Agent Skills: Ready "), "agent-skills-ready");
});
