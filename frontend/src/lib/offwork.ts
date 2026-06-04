import type { CalendarInfo, RestDayKind } from "./types";

const CHINA_TIME_ZONE = "Asia/Shanghai";
const OFF_WORK_HOUR = 18;
const OFF_WORK_MINUTE = 0;

export type OffWorkReason = Exclude<RestDayKind, "workday"> | "after-hours";

export interface OffWorkStatus {
  closed: boolean;
  countdown?: string;
  reason?: OffWorkReason;
}

export interface OffWorkTime {
  hour: number;
  minute: number;
}

function getChinaTimeParts(date: Date): { h: number; m: number; s: number } {
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: CHINA_TIME_ZONE,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
  }).formatToParts(date);
  const h = Number(parts.find((p) => p.type === "hour")?.value ?? "0");
  const m = Number(parts.find((p) => p.type === "minute")?.value ?? "0");
  const s = Number(parts.find((p) => p.type === "second")?.value ?? "0");
  return { h, m, s };
}

function pad2(n: number): string {
  return String(n).padStart(2, "0");
}

export function getOffWorkStatus(
  date: Date = new Date(),
  calendar: Pick<CalendarInfo, "isRestDay" | "kind"> = { isRestDay: false, kind: "workday" },
  offWorkTime: OffWorkTime = { hour: OFF_WORK_HOUR, minute: OFF_WORK_MINUTE },
): OffWorkStatus {
  if (calendar.isRestDay) {
    return { closed: true, reason: calendar.kind === "holiday" ? "holiday" : "weekend" };
  }

  const { h, m, s } = getChinaTimeParts(date);
  const remaining = (offWorkTime.hour - h) * 3600 + (offWorkTime.minute - m) * 60 - s;
  if (remaining <= 0) {
    return { closed: true, reason: "after-hours" };
  }

  const hh = Math.floor(remaining / 3600);
  const mm = Math.floor((remaining % 3600) / 60);
  const ss = remaining % 60;
  return { closed: false, countdown: `${pad2(hh)}:${pad2(mm)}:${pad2(ss)}` };
}
