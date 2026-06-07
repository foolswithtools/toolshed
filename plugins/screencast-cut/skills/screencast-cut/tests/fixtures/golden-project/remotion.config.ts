// Minimal Remotion CLI config. Not part of the bundle graph — only the CLI
// reads it. Phase 1 of the skills checks for this file to detect a scaffolded
// project.
import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.overrideWebpackConfig((config) => config);
