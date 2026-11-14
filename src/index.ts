import { Context, Schema } from 'cordis';
import * as fs from 'fs';
import * as path from 'path';

export interface ServerMeta {
  displayName?: string;
  category?: string;
  description?: string;
  toolsCount?: number;
  tags?: string[];
  intentPatterns?: string[];
  serverConfig: any;
}

export interface RegistryConfig {
  version?: string;
  default_profile?: string;
  profiles?: Record<string, string[]>;
  servers: Record<string, ServerMeta>;
}

export interface PluginConfig {
  registryPath?: string;
  autoMount?: boolean;
  scoreThreshold?: number;
  keepAliveTurns?: number;
}

export const Config: Schema<PluginConfig> = Schema.object({
  registryPath: Schema.string().description('Path to mcp_registry.json asset map').default('mcp_registry.json'),
  autoMount: Schema.boolean().description('Automatically mount matched MCP servers just-in-time').default(true),
  scoreThreshold: Schema.number().description('Minimum match score required to trigger mounting').default(3),
  keepAliveTurns: Schema.number().description('Number of conversation turns a mounted server remains active').default(2),
});

export const name = 'mcp-map-router';

export function apply(ctx: Context, config: PluginConfig) {
  const logger = ctx.logger('mcp-map-router');
  let registry: RegistryConfig = { servers: {} };

  // 1. Resolve and load Asset Map
  const resolveRegistry = (): RegistryConfig => {
    const targetPath = config.registryPath || 'mcp_registry.json';
    const resolved = path.isAbsolute(targetPath) ? targetPath : path.resolve(process.cwd(), targetPath);
    if (!fs.existsSync(resolved)) {
      logger.warn(`Asset map not found at ${resolved}. Router running in standby mode.`);
      return { servers: {} };
    }
    try {
      const raw = fs.readFileSync(resolved, 'utf-8');
      return JSON.parse(raw);
    } catch (err) {
      logger.error(`Failed to parse asset map at ${resolved}:`, err);
      return { servers: {} };
    }
  };

  registry = resolveRegistry();

  // Internal active tracker
  const activeMounts = new Map<string, number>(); // serverName -> turnsRemaining

  /**
   * Scan prompt against Asset Map metadata
   */
  const scanIntent = (prompt: string): Array<{ name: string; score: number; meta: ServerMeta }> => {
    const text = prompt.toLowerCase();
    const results: Array<{ name: string; score: number; meta: ServerMeta }> = [];

    for (const [name, meta] of Object.entries(registry.servers || {})) {
      let score = 0;
      for (const tag of meta.tags || []) {
        if (text.includes(tag.toLowerCase())) {
          score += 2;
        }
      }
      for (const pattern of meta.intentPatterns || []) {
        try {
          if (text.includes(pattern.toLowerCase()) || new RegExp(pattern, 'i').test(text)) {
            score += 3;
          }
        } catch {
          if (text.includes(pattern.toLowerCase())) score += 3;
        }
      }
      if (score >= (config.scoreThreshold || 3)) {
        results.push({ name, score, meta });
      }
    }

    return results.sort((a, b) => b.score - a.score);
  };

  // Register DSH CLI / chat command for manual control
  if ((ctx as any).command) {
    (ctx as any).command('mcp <subcommand> [arg]', 'Manage MCP Asset Map and Profiles')
      .action(async ({ session }: any, subcommand: string, arg: string) => {
        if (subcommand === 'status') {
          const total = Object.keys(registry.servers || {}).length;
          const active = Array.from(activeMounts.keys());
          return `[MCP Map Router] Total Assets: ${total} | Active JIT Mounts: ${active.length > 0 ? active.join(', ') : 'None'}`;
        }
        if (subcommand === 'list') {
          const profiles = Object.keys(registry.profiles || {}).join(', ');
          return `Available Profiles: ${profiles}`;
        }
        if (subcommand === 'scan' && arg) {
          const matches = scanIntent(arg);
          if (matches.length === 0) return `No matches found for intent: "${arg}"`;
          return matches.map(m => `★ [${m.score} pts] ${m.name} (${m.meta.displayName || 'Server'})`).join('\n');
        }
        return 'Usage: mcp [status|list|scan <prompt>]';
      });
  }

  // Hook into Agent lifecycle turn (DeepSeek Harness / Cordis event)
  ctx.on('before-send' as any, async (session: any) => {
    // Decay active mounts
    for (const [name, turns] of Array.from(activeMounts.entries())) {
      if (turns <= 1) {
        activeMounts.delete(name);
        logger.info(`Auto-detached JIT MCP server: ${name} (context preserved)`);
      } else {
        activeMounts.set(name, turns - 1);
      }
    }
  });

  // Intent interceptor before agent execution
  ctx.on('middleware' as any, async (session: any, next: () => Promise<any>) => {
    const input = session?.content || '';
    if (config.autoMount && input.length > 0) {
      const matches = scanIntent(input);
      if (matches.length > 0) {
        const top = matches[0];
        if (!activeMounts.has(top.name)) {
          activeMounts.set(top.name, config.keepAliveTurns || 2);
          logger.info(`[JIT Mount] Matched intent "${input.slice(0, 30)}..." -> Mounting "${top.name}"`);
          // Notify Cordis / DSH tool registry if available
          if ((ctx as any).emit) {
            (ctx as any).emit('mcp/mount-server', top.name, top.meta.serverConfig);
          }
        }
      }
    }
    return next();
  });

  logger.info(`MCP Map-First Router initialized with ${Object.keys(registry.servers || {}).length} asset specifications.`);
}
