import { describe, expect, test, beforeAll } from "bun:test";
import { EmbeddingsService } from "../src/services/embeddings.service";
import {
  isModelAvailable,
  createEmbeddingsService,
  testWithModel,
} from "./utils/model-loader";

describe("EmbeddingsService", () => {
  let service: EmbeddingsService;

  beforeAll(() => {
    if (isModelAvailable()) {
      service = createEmbeddingsService();
    }
  });

  describe("constructor", () => {
    test("sets dimension from constructor", () => {
      const s = new EmbeddingsService("Xenova/all-MiniLM-L6-v2", 384);
      expect(s.dimension).toBe(384);
    });
  });

  describe("dimension", () => {
    testWithModel("returns configured dimension", () => {
      expect(service.dimension).toBe(384);
    });
  });

  describe("embed", () => {
    testWithModel("returns array of correct dimension", async () => {
      const embedding = await service.embed("hello world");
      expect(embedding).toBeArray();
      expect(embedding.length).toBe(384);
    });

    testWithModel("returns numbers in reasonable range", async () => {
      const embedding = await service.embed("test text");
      for (const value of embedding) {
        expect(typeof value).toBe("number");
        expect(Math.abs(value)).toBeLessThan(10);
      }
    });

    testWithModel("produces different embeddings for different texts", async () => {
      const embedding1 = await service.embed("hello world");
      const embedding2 = await service.embed("goodbye universe");

      let hasDifference = false;
      for (let i = 0; i < embedding1.length; i++) {
        if (Math.abs(embedding1[i] - embedding2[i]) > 0.01) {
          hasDifference = true;
          break;
        }
      }
      expect(hasDifference).toBe(true);
    });

    testWithModel("produces similar embeddings for similar texts", async () => {
      const embedding1 = await service.embed("the cat sat on the mat");
      const embedding2 = await service.embed("a cat sitting on a mat");

      let dotProduct = 0;
      let norm1 = 0;
      let norm2 = 0;
      for (let i = 0; i < embedding1.length; i++) {
        dotProduct += embedding1[i] * embedding2[i];
        norm1 += embedding1[i] * embedding1[i];
        norm2 += embedding2[i] * embedding2[i];
      }
      const similarity = dotProduct / (Math.sqrt(norm1) * Math.sqrt(norm2));

      expect(similarity).toBeGreaterThan(0.8);
    });
  });

  describe("embedBatch", () => {
    testWithModel("returns array of embeddings", async () => {
      const embeddings = await service.embedBatch(["hello", "world"]);
      expect(embeddings).toBeArray();
      expect(embeddings.length).toBe(2);
      expect(embeddings[0].length).toBe(384);
      expect(embeddings[1].length).toBe(384);
    });

    testWithModel("handles empty array", async () => {
      const embeddings = await service.embedBatch([]);
      expect(embeddings).toBeArray();
      expect(embeddings.length).toBe(0);
    });

    testWithModel("produces same results as individual embed calls", async () => {
      const texts = ["hello", "world"];
      const batchEmbeddings = await service.embedBatch(texts);
      const individualEmbeddings = await Promise.all(
        texts.map((t) => service.embed(t))
      );

      for (let i = 0; i < texts.length; i++) {
        for (let j = 0; j < 384; j++) {
          expect(batchEmbeddings[i][j]).toBeCloseTo(individualEmbeddings[i][j], 5);
        }
      }
    });
  });
});
