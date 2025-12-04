import {
  Schema,
  Field,
  FixedSizeList,
  Float32,
  Utf8,
  Timestamp,
  TimeUnit,
} from "apache-arrow";

export const TABLE_NAME = "memories";

export const memorySchema = new Schema([
  new Field("id", new Utf8(), false),
  new Field(
    "vector",
    new FixedSizeList(384, new Field("item", new Float32())),
    false
  ),
  new Field("content", new Utf8(), false),
  new Field("metadata", new Utf8(), false), // JSON string
  new Field(
    "created_at",
    new Timestamp(TimeUnit.MILLISECOND),
    false
  ),
  new Field(
    "updated_at",
    new Timestamp(TimeUnit.MILLISECOND),
    false
  ),
  new Field("superseded_by", new Utf8(), true), // Nullable
]);
