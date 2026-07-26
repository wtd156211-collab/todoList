import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { expect, it } from 'vitest';

const appConfigPath = resolve(process.cwd(), 'miniprogram', 'app.json');

it('registers the six Flowlist MVP pages', () => {
  expect(existsSync(appConfigPath)).toBe(true);

  const config = JSON.parse(readFileSync(appConfigPath, 'utf8')) as { pages: string[] };
  expect(config.pages).toHaveLength(6);
});
