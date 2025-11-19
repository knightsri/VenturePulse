import { exec } from 'child_process';
import fs from 'fs';
import path from 'path';
import { promisify } from 'util';
import { AnalysisJobData, JobProgress } from '../types';

const execAsync = promisify(exec);

export class ReportGenerator {
  private static readonly REPORTS_DIR = '/app/reports';
  private static readonly SCRIPTS_DIR = '/app/scripts';
  private static readonly PROMPTS_DIR = '/app/prompts';

  /**
   * Generate a complete analysis report using analyze-script.sh
   */
  static async generateReport(
    job: AnalysisJobData,
    onProgress?: (progress: JobProgress) => void
  ): Promise<string> {
    const { projectName, projectContent, model } = job;

    // Create temp file for project content
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const sanitizedName = projectName.replace(/[^a-zA-Z0-9-]/g, '-').toLowerCase();
    const projectFileName = `${sanitizedName}-${timestamp}.md`;
    const tempDir = path.join('/tmp', `venturepulse-${job.jobId}`);
    const projectFilePath = path.join(tempDir, projectFileName);

    try {
      // Create temp directory
      fs.mkdirSync(tempDir, { recursive: true });

      // Write project content to file
      fs.writeFileSync(projectFilePath, projectContent);

      console.log(`[ReportGenerator] Starting analysis for ${projectName} with model ${model}`);
      console.log(`[ReportGenerator] Project file: ${projectFilePath}`);

      // Execute analyze-script.sh
      const reportPath = await this.executeAnalysisScript(
        projectFilePath,
        model,
        (section, total) => {
          if (onProgress) {
            onProgress({
              currentSection: section,
              totalSections: total,
              sectionName: this.getSectionName(section),
              percentage: Math.round((section / total) * 100),
            });
          }
        }
      );

      console.log(`[ReportGenerator] Analysis complete. Report saved to: ${reportPath}`);

      // Clean up temp file
      fs.rmSync(tempDir, { recursive: true, force: true });

      return reportPath;
    } catch (error) {
      console.error('[ReportGenerator] Error generating report:', error);

      // Clean up on error
      if (fs.existsSync(tempDir)) {
        fs.rmSync(tempDir, { recursive: true, force: true });
      }

      throw new Error(`Report generation failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Execute the analyze-script.sh with the given parameters
   */
  private static async executeAnalysisScript(
    projectFilePath: string,
    model: string,
    onProgress: (section: number, total: number) => void
  ): Promise<string> {
    const scriptPath = path.join(this.SCRIPTS_DIR, 'analyze-script.sh');

    // Prepare environment variables
    const env = {
      ...process.env,
      OPENROUTER_API_KEY: process.env.OPENROUTER_API_KEY,
      PATH: process.env.PATH,
    };

    // Execute script
    const command = `bash "${scriptPath}" "${projectFilePath}" "${model}"`;

    console.log(`[ReportGenerator] Executing: ${command}`);

    return new Promise((resolve, reject) => {
      const child = exec(command, {
        env,
        maxBuffer: 10 * 1024 * 1024, // 10MB buffer
        timeout: 30 * 60 * 1000, // 30 minute timeout
      });

      let stdout = '';
      let stderr = '';
      let currentSection = 0;
      const totalSections = 9;

      child.stdout?.on('data', (data) => {
        stdout += data;
        const output = data.toString();

        // Parse progress from script output
        // Look for patterns like "Section 3/9" or "Generating section 3"
        const sectionMatch = output.match(/section\s+(\d+)/i);
        if (sectionMatch) {
          const section = parseInt(sectionMatch[1]);
          if (section > currentSection && section <= totalSections) {
            currentSection = section;
            onProgress(currentSection, totalSections);
          }
        }

        console.log(`[Script] ${output.trim()}`);
      });

      child.stderr?.on('data', (data) => {
        stderr += data;
        console.error(`[Script Error] ${data.toString().trim()}`);
      });

      child.on('close', (code) => {
        if (code === 0) {
          // Extract report path from stdout
          const reportPath = this.extractReportPath(stdout, projectFilePath);
          resolve(reportPath);
        } else {
          reject(new Error(`Script exited with code ${code}\nStderr: ${stderr}`));
        }
      });

      child.on('error', (error) => {
        reject(error);
      });
    });
  }

  /**
   * Extract the generated report path from script output
   */
  private static extractReportPath(stdout: string, projectFilePath: string): string {
    // The analyze-script.sh creates a directory based on the project file name and timestamp
    // Pattern: project-name-analysis-model-YYYYMMDD-HHMMSS

    const projectFileName = path.basename(projectFilePath, '.md');
    const reportDirs = fs.readdirSync(this.REPORTS_DIR);

    // Find the most recent directory matching the project name
    const matchingDirs = reportDirs
      .filter(dir => dir.includes(projectFileName.split('-')[0]))
      .sort()
      .reverse();

    if (matchingDirs.length > 0) {
      return path.join(this.REPORTS_DIR, matchingDirs[0]);
    }

    // Fallback: try to find any new directory
    const allDirs = reportDirs.map(dir => ({
      name: dir,
      path: path.join(this.REPORTS_DIR, dir),
      time: fs.statSync(path.join(this.REPORTS_DIR, dir)).mtime.getTime(),
    }));

    allDirs.sort((a, b) => b.time - a.time);

    if (allDirs.length > 0) {
      return allDirs[0].path;
    }

    throw new Error('Could not locate generated report directory');
  }

  /**
   * Get section name by number
   */
  private static getSectionName(section: number): string {
    const sections = [
      'Executive Summary',
      'Market Landscape',
      'Technical Feasibility',
      'Competitive Advantage',
      'Business Model',
      'MVP Roadmap',
      'Success Metrics',
      'Go-to-Market',
      'Risk Analysis',
    ];

    return sections[section - 1] || `Section ${section}`;
  }

  /**
   * Check if analyze-script.sh is available and executable
   */
  static async checkScriptAvailability(): Promise<boolean> {
    const scriptPath = path.join(this.SCRIPTS_DIR, 'analyze-script.sh');

    try {
      fs.accessSync(scriptPath, fs.constants.X_OK);
      return true;
    } catch {
      console.error(`[ReportGenerator] Script not found or not executable: ${scriptPath}`);
      return false;
    }
  }
}
