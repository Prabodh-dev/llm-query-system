const LEVELS = { debug: 10, info: 20, warn: 30, error: 40 };

export function createLogger({ level = "info", stream = process.stdout } = {}) {
  const threshold = LEVELS[level] ?? LEVELS.info;
  const write = (name) => (msg, fields = {}) => {
    if (LEVELS[name] < threshold) return;
    stream.write(
      JSON.stringify({ ts: new Date().toISOString(), level: name, msg, ...fields }) + "\n"
    );
  };
  return { debug: write("debug"), info: write("info"), warn: write("warn"), error: write("error") };
}
