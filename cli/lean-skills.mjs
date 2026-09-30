#!/usr/bin/env node
// Syncs skills between this repo and a project's .claude/skills folder.
// Only depends on Node (18+) and git; uses the git credentials you already have.

import { execFileSync } from 'node:child_process';
import { cpSync, existsSync, mkdtempSync, readdirSync, readFileSync, rmSync, mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { basename, join } from 'node:path';

const REPO_URL = process.env.LEAN_SKILLS_REPO ?? 'https://github.com/E-MDawood/lean-ai-skills.git';
const BASE_BRANCH = process.env.LEAN_SKILLS_BRANCH ?? 'main';
const CATEGORIES = ['common', 'frontend', 'backend'];
const IGNORED = new Set(['node_modules', '.DS_Store', '.git']);
const LOCAL_SKILLS_DIR = join(process.cwd(), '.claude', 'skills');

const USAGE = `Usage:
  lean-skills pull [--frontend] [--backend]
      Copy common skills plus frontend and/or backend skills into ./.claude/skills.
      Skills with the same name are replaced; other local skills are left alone.

  lean-skills push --type <common|frontend|backend> --name <skill-name>
      Upload ./.claude/skills/<skill-name> to <type>/<skill-name> in the repo and open a
      pull request. A skill with the same name anywhere in the repo is replaced.

Environment:
  LEAN_SKILLS_REPO    Git URL of the skills repo (default: ${REPO_URL})
  LEAN_SKILLS_BRANCH  Base branch (default: ${BASE_BRANCH})`;

function fail(message) {
  console.error(`Error: ${message}\n\n${USAGE}`);
  process.exit(1);
}

function git(args, cwd, { quiet = true } = {}) {
  return execFileSync('git', args, { cwd, encoding: 'utf8', stdio: quiet ? 'pipe' : 'inherit' });
}

function hasCommand(cmd) {
  try {
    execFileSync(cmd, ['--version'], { stdio: 'ignore' });
    return true;
  } catch {
    return false;
  }
}

function cloneRepo() {
  const dir = mkdtempSync(join(tmpdir(), 'lean-skills-'));
  console.log(`Fetching ${REPO_URL} (${BASE_BRANCH})...`);
  try {
    git(['clone', '--depth', '1', '--branch', BASE_BRANCH, REPO_URL, dir]);
  } catch (err) {
    rmSync(dir, { recursive: true, force: true });
    fail(`could not clone the skills repo.\n${err.stderr ?? err.message}`);
  }
  return dir;
}

function copySkill(from, to) {
  rmSync(to, { recursive: true, force: true });
  cpSync(from, to, { recursive: true, filter: (src) => !IGNORED.has(basename(src)) });
}

function listSkills(categoryDir) {
  if (!existsSync(categoryDir)) return [];
  return readdirSync(categoryDir, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && existsSync(join(categoryDir, entry.name, 'SKILL.md')))
    .map((entry) => entry.name);
}

function parseArgs(argv) {
  const flags = {};
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (!arg.startsWith('--')) fail(`unexpected argument "${arg}"`);
    const [key, inline] = arg.slice(2).split('=', 2);
    if (inline !== undefined) flags[key] = inline;
    else if (argv[i + 1] && !argv[i + 1].startsWith('--')) flags[key] = argv[++i];
    else flags[key] = true;
  }
  return flags;
}

function pull(flags) {
  if (!flags.frontend && !flags.backend) fail('pass --frontend, --backend or both');
  const categories = ['common', flags.frontend && 'frontend', flags.backend && 'backend'].filter(Boolean);

  const repoDir = cloneRepo();
  try {
    mkdirSync(LOCAL_SKILLS_DIR, { recursive: true });
    for (const category of categories) {
      const skills = listSkills(join(repoDir, category));
      for (const skill of skills) {
        const replaced = existsSync(join(LOCAL_SKILLS_DIR, skill));
        copySkill(join(repoDir, category, skill), join(LOCAL_SKILLS_DIR, skill));
        console.log(`  ${replaced ? 'updated' : 'added  '} ${category}/${skill}`);
      }
    }
    console.log(`Done. Skills are in ${LOCAL_SKILLS_DIR}`);
  } finally {
    rmSync(repoDir, { recursive: true, force: true });
  }
}

function frontmatterName(skillFile) {
  const match = readFileSync(skillFile, 'utf8').match(/^---\s*\n([\s\S]*?)\n---/);
  return match?.[1].match(/^name:\s*["']?([^"'\n]+?)["']?\s*$/m)?.[1];
}

function compareUrl(branch) {
  const match = REPO_URL.match(/github\.com[:/](.+?)(?:\.git)?$/);
  return match ? `https://github.com/${match[1]}/compare/${BASE_BRANCH}...${branch}?expand=1` : undefined;
}

function push(flags) {
  const { type, name } = flags;
  if (!CATEGORIES.includes(type)) fail(`--type must be one of: ${CATEGORIES.join(', ')}`);
  if (typeof name !== 'string' || !/^[a-z0-9]+(-[a-z0-9]+)*$/.test(name)) fail('--name must be a kebab-case skill name');

  const localSkill = join(LOCAL_SKILLS_DIR, name);
  const skillFile = join(localSkill, 'SKILL.md');
  if (!existsSync(skillFile)) fail(`${skillFile} not found`);

  const declaredName = frontmatterName(skillFile);
  if (declaredName && declaredName !== name) {
    console.warn(`Warning: SKILL.md declares name "${declaredName}" but the folder is "${name}".`);
  }

  const repoDir = cloneRepo();
  try {
    const previous = CATEGORIES.filter((category) => existsSync(join(repoDir, category, name)));
    for (const category of previous) rmSync(join(repoDir, category, name), { recursive: true, force: true });
    copySkill(localSkill, join(repoDir, type, name));

    git(['add', '-A'], repoDir);
    if (!git(['status', '--porcelain'], repoDir).trim()) {
      console.log(`No changes: ${type}/${name} in the repo already matches your local copy.`);
      return;
    }

    const action = previous.length ? 'update' : 'add';
    const moved = previous.filter((category) => category !== type);
    const branch = `skill/${name}-${Date.now()}`;
    const title = `feat(skills): ${action} ${name}`;
    const body = [
      `${action === 'add' ? 'Adds' : 'Updates'} the \`${name}\` skill in \`${type}/\`.`,
      moved.length ? `Moved from \`${moved.join(', ')}/\`.` : '',
      action === 'add' ? 'Remember to add it to the skills table in README.md.' : '',
      '',
      'Pushed with `lean-skills push`.',
    ].filter((line, i, all) => line || all[i - 1]).join('\n');

    git(['checkout', '-b', branch], repoDir);
    git(['commit', '-m', title, '-m', body], repoDir);
    console.log(`Pushing branch ${branch}...`);
    git(['push', '-u', 'origin', branch], repoDir, { quiet: false });

    if (hasCommand('gh')) {
      execFileSync('gh', ['pr', 'create', '--base', BASE_BRANCH, '--head', branch, '--title', title, '--body', body], {
        cwd: repoDir,
        stdio: 'inherit',
      });
    } else {
      const url = compareUrl(branch);
      console.log(`\nOpen the pull request here:\n  ${url ?? `(open a PR from ${branch} into ${BASE_BRANCH})`}`);
    }
  } finally {
    rmSync(repoDir, { recursive: true, force: true });
  }
}

const [command, ...rest] = process.argv.slice(2);
if (!command || command === '--help' || command === '-h') {
  console.log(USAGE);
} else if (command === 'pull') {
  pull(parseArgs(rest));
} else if (command === 'push') {
  push(parseArgs(rest));
} else {
  fail(`unknown command "${command}"`);
}
