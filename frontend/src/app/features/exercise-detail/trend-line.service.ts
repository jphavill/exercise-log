import { Injectable } from '@angular/core';

type LineFit = {
  slope: number;
  intercept: number;
  sse: number;
  values: number[];
};

export type SegmentedTrendResult = {
  values: number[];
  breakIndex: number | null;
};

@Injectable({ providedIn: 'root' })
export class TrendLineService {
  private readonly minSegmentLength = 7;
  private readonly minimumImprovementRatio = 0.3;

  buildSegmentedTrend(values: number[]): SegmentedTrendResult {
    if (values.length < 2) {
      return { values: [...values], breakIndex: null };
    }

    const singleLine = this.fitRange(values, 0, values.length);
    if (values.length < this.minSegmentLength * 2) {
      return { values: singleLine.values, breakIndex: null };
    }

    let bestBreakIndex: number | null = null;
    let bestLeft: LineFit | null = null;
    let bestRight: LineFit | null = null;
    let bestSegmentedSse = Number.POSITIVE_INFINITY;

    for (let breakIndex = this.minSegmentLength; breakIndex <= values.length - this.minSegmentLength; breakIndex += 1) {
      const left = this.fitRange(values, 0, breakIndex);
      const right = this.fitRange(values, breakIndex, values.length);
      const segmentedSse = left.sse + right.sse;
      if (segmentedSse < bestSegmentedSse) {
        bestSegmentedSse = segmentedSse;
        bestBreakIndex = breakIndex;
        bestLeft = left;
        bestRight = right;
      }
    }

    if (bestBreakIndex == null || !bestLeft || !bestRight) {
      return { values: singleLine.values, breakIndex: null };
    }

    const improvedEnough = this.isImprovedEnough(singleLine.sse, bestSegmentedSse);
    const changedEnough = this.hasMeaningfulChange(values, bestBreakIndex, bestLeft, bestRight);

    if (!improvedEnough || !changedEnough) {
      return { values: singleLine.values, breakIndex: null };
    }

    return {
      values: [...bestLeft.values, ...bestRight.values],
      breakIndex: bestBreakIndex,
    };
  }

  private isImprovedEnough(singleSse: number, segmentedSse: number): boolean {
    if (singleSse <= 0) {
      return false;
    }
    const improvementRatio = (singleSse - segmentedSse) / singleSse;
    return improvementRatio >= this.minimumImprovementRatio;
  }

  private hasMeaningfulChange(values: number[], breakIndex: number, left: LineFit, right: LineFit): boolean {
    const minimumSlopeChange = this.minimumSlopeChange(values.length, values);
    const minimumLevelChange = this.minimumLevelChange(values);
    const slopeDelta = Math.abs(left.slope - right.slope);
    const levelAtBreakDelta = Math.abs(this.predictAt(left, breakIndex) - this.predictAt(right, breakIndex));
    return slopeDelta >= minimumSlopeChange || levelAtBreakDelta >= minimumLevelChange;
  }

  private minimumSlopeChange(length: number, values: number[]): number {
    const dataRange = this.range(values);
    const baselineSlope = dataRange / Math.max(1, length - 1);
    return Math.max(0.05, baselineSlope * 0.35);
  }

  private minimumLevelChange(values: number[]): number {
    const dataRange = this.range(values);
    return Math.max(1, dataRange * 0.2);
  }

  private fitRange(values: number[], start: number, end: number): LineFit {
    const count = end - start;
    if (count <= 0) {
      return { slope: 0, intercept: 0, sse: 0, values: [] };
    }

    let sumX = 0;
    let sumY = 0;
    let sumXX = 0;
    let sumXY = 0;

    for (let x = start; x < end; x += 1) {
      const y = values[x];
      sumX += x;
      sumY += y;
      sumXX += x * x;
      sumXY += x * y;
    }

    const denominator = count * sumXX - sumX * sumX;
    const slope = denominator === 0 ? 0 : (count * sumXY - sumX * sumY) / denominator;
    const intercept = (sumY - slope * sumX) / count;

    const fittedValues: number[] = [];
    let sse = 0;
    for (let x = start; x < end; x += 1) {
      const predicted = slope * x + intercept;
      fittedValues.push(predicted);
      const error = values[x] - predicted;
      sse += error * error;
    }

    return {
      slope,
      intercept,
      sse,
      values: fittedValues,
    };
  }

  private predictAt(line: LineFit, x: number): number {
    return line.slope * x + line.intercept;
  }

  private range(values: number[]): number {
    if (!values.length) {
      return 0;
    }

    let min = values[0];
    let max = values[0];
    for (const value of values) {
      if (value < min) {
        min = value;
      }
      if (value > max) {
        max = value;
      }
    }
    return max - min;
  }
}
