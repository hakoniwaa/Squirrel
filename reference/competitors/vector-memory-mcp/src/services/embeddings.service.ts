import { pipeline, type FeatureExtractionPipeline } from "@huggingface/transformers";

export class EmbeddingsService {
  private modelName: string;
  private extractor: FeatureExtractionPipeline | null = null;
  private initPromise: Promise<FeatureExtractionPipeline> | null = null;
  private _dimension: number;

  constructor(modelName: string, dimension: number) {
    this.modelName = modelName;
    this._dimension = dimension;
  }

  get dimension(): number {
    return this._dimension;
  }

  private async getExtractor(): Promise<FeatureExtractionPipeline> {
    if (this.extractor) {
      return this.extractor;
    }

    if (!this.initPromise) {
      this.initPromise = pipeline("feature-extraction", this.modelName, {
        quantized: true,
      }) as Promise<FeatureExtractionPipeline>;
    }

    this.extractor = await this.initPromise;
    return this.extractor;
  }

  async embed(text: string): Promise<number[]> {
    const extractor = await this.getExtractor();
    const output = await extractor(text, { pooling: "mean", normalize: true });
    return Array.from(output.data as Float32Array);
  }

  async embedBatch(texts: string[]): Promise<number[][]> {
    const results: number[][] = [];
    for (const text of texts) {
      results.push(await this.embed(text));
    }
    return results;
  }
}
