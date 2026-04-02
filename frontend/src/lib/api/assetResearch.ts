import { requestJson } from "./client";
import type {
  AskAssetResearchQuestionRequest,
  AskAssetResearchQuestionResponse,
  GenerateAssetMemoRequest,
  GenerateAssetMemoResponse
} from "./types";

export function generateAssetResearchMemo(
  payload: GenerateAssetMemoRequest
): Promise<GenerateAssetMemoResponse> {
  return requestJson<GenerateAssetMemoResponse>("/asset-research/memos", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function askAssetResearchQuestion(
  payload: AskAssetResearchQuestionRequest
): Promise<AskAssetResearchQuestionResponse> {
  return requestJson<AskAssetResearchQuestionResponse>("/asset-research/questions", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
