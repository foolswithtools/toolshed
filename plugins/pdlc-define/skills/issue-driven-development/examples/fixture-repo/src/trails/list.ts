// Fictional fixture module for the issue-driven-development worked
// examples. Not real product code.
//
// Trail listing endpoint: returns the trail catalog for a tenant, paginated.
import { Request, Response } from "./http-types";
import { listTrailsForTenant } from "./data";

export interface TrailSummary {
  id: string;
  name: string;
  distanceMeters: number;
  stage: "draft" | "published" | "archived";
}

export async function listTrailsHandler(req: Request, res: Response) {
  const tenantId = req.tenantId;
  const stage = req.query.stage;
  const trails = await listTrails(tenantId, stage);
  res.json({ trails });
}

export async function listTrails(
  tenantId: string,
  stage?: string
): Promise<TrailSummary[]> {
  return listTrailsForTenant(tenantId, stage);
}
