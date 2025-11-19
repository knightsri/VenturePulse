import fs from 'fs';
import mammoth from 'mammoth';
import pdfParse from 'pdf-parse';

export class FileProcessor {
  /**
   * Extract text content from uploaded file based on file type
   */
  static async extractText(filePath: string, mimeType: string): Promise<string> {
    const extension = filePath.split('.').pop()?.toLowerCase();

    try {
      switch (extension) {
        case 'txt':
        case 'md':
          return await this.extractTextFile(filePath);

        case 'docx':
          return await this.extractDocx(filePath);

        case 'pdf':
          return await this.extractPdf(filePath);

        default:
          throw new Error(`Unsupported file type: ${extension}`);
      }
    } catch (error) {
      console.error('[FileProcessor] Error extracting text:', error);
      throw new Error(`Failed to extract text from file: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Extract text from .txt or .md files
   */
  private static async extractTextFile(filePath: string): Promise<string> {
    const content = fs.readFileSync(filePath, 'utf-8');
    return content.trim();
  }

  /**
   * Extract text from .docx files using mammoth
   */
  private static async extractDocx(filePath: string): Promise<string> {
    const result = await mammoth.extractRawText({ path: filePath });
    return result.value.trim();
  }

  /**
   * Extract text from .pdf files using pdf-parse
   */
  private static async extractPdf(filePath: string): Promise<string> {
    const dataBuffer = fs.readFileSync(filePath);
    const data = await pdfParse(dataBuffer);
    return data.text.trim();
  }

  /**
   * Validate file type
   */
  static isValidFileType(mimeType: string, filename: string): boolean {
    const validExtensions = ['txt', 'md', 'docx', 'pdf'];
    const extension = filename.split('.').pop()?.toLowerCase();
    return validExtensions.includes(extension || '');
  }

  /**
   * Validate file size
   */
  static isValidFileSize(sizeInBytes: number): boolean {
    const maxSizeMB = parseInt(process.env.MAX_UPLOAD_SIZE_MB || '10');
    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    return sizeInBytes <= maxSizeBytes;
  }

  /**
   * Validate content length
   */
  static isValidContentLength(content: string): { valid: boolean; message?: string } {
    const minLength = 100;
    const maxLength = 50000; // ~50k characters

    if (content.length < minLength) {
      return {
        valid: false,
        message: `Content too short. Minimum ${minLength} characters required, got ${content.length}`,
      };
    }

    if (content.length > maxLength) {
      return {
        valid: false,
        message: `Content too long. Maximum ${maxLength} characters allowed, got ${content.length}`,
      };
    }

    return { valid: true };
  }
}
