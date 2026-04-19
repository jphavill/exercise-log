import { Injectable } from '@angular/core';

type RegressionModel = {
  slope: number;
  intercept: number;
};

type TrendLineOptions = {
  minSegmentLength: number;
  absoluteThreshold: number;
  percentThreshold: number;
  breakPersistence: number;
  minPercentBase: number;
};

export type TrendSegment = {
  startIndex: number;
  endIndex: number;
  slope: number;
  intercept: number;
};

export type SegmentedTrendResult = {
  values: number[];
  breakIndex: number | null;
  breakIndices: number[];
  segments: TrendSegment[];
};

@Injectable({ providedIn: 'root' })
export class TrendLineService {
  private readonly defaultOptions: TrendLineOptions = {
    minSegmentLength: 4,
    absoluteThreshold: 12,
    percentThreshold: 0.35,
    breakPersistence: 2,
    minPercentBase: 10,
  };

  buildSegmentedTrend(values: number[], options: Partial<TrendLineOptions> = {}): SegmentedTrendResult {
    const config = { ...this.defaultOptions, ...options };
    if (values.length < 2) {
      return {
        values: [...values],
        breakIndex: null,
        breakIndices: [],
        segments: [
          {
            startIndex: 0,
            endIndex: values.length,
            slope: 0,
            intercept: values[0] ?? 0,
          },
        ],
      };
    }

    const breakIndices: number[] = [];
    const segments: TrendSegment[] = [];
    let segmentStart = 0;
    let index = config.minSegmentLength;
    let candidateBreakIndex: number | null = null;
    let candidateModel: RegressionModel | null = null;
    let candidateDirection = 0;
    let confirmations = 0;

    while (index < values.length) {
      const hasEnoughPoints = index - segmentStart >= config.minSegmentLength;
      if (!hasEnoughPoints) {
        index += 1;
        continue;
      }

      const model = candidateBreakIndex == null ? this.fitLinearRegression(values, segmentStart, index) : candidateModel;
      if (!model) {
        index += 1;
        continue;
      }
      const predicted = this.predict(model, index - segmentStart);
      const residual = Math.abs(values[index] - predicted);
      const direction = Math.sign(values[index] - predicted);

      if (this.shouldBreakSegment(residual, predicted, config)) {
        if (candidateBreakIndex == null) {
          candidateBreakIndex = index;
          candidateModel = this.fitLinearRegression(values, segmentStart, index);
          candidateDirection = direction;
          confirmations = 1;
        } else if (direction === candidateDirection) {
          confirmations += 1;
        } else {
          candidateBreakIndex = index;
          candidateModel = this.fitLinearRegression(values, segmentStart, index);
          candidateDirection = direction;
          confirmations = 1;
        }

        const candidate = candidateBreakIndex;
        const isConfirmed =
          confirmations >= config.breakPersistence &&
          candidate - segmentStart >= config.minSegmentLength &&
          values.length - candidate >= config.minSegmentLength &&
          this.hasSustainedLevelShift(values, candidate, config);

        if (isConfirmed) {
          const segmentModel = this.fitLinearRegression(values, segmentStart, candidate);
          segments.push({
            startIndex: segmentStart,
            endIndex: candidate,
            slope: segmentModel.slope,
            intercept: segmentModel.intercept,
          });
          breakIndices.push(candidate);
          segmentStart = candidate;
          index = segmentStart + config.minSegmentLength;
          candidateBreakIndex = null;
          candidateModel = null;
          candidateDirection = 0;
          confirmations = 0;
          continue;
        }
      } else {
        candidateBreakIndex = null;
        candidateModel = null;
        candidateDirection = 0;
        confirmations = 0;
      }

      index += 1;
    }

    const finalSegmentModel = this.fitLinearRegression(values, segmentStart, values.length);
    segments.push({
      startIndex: segmentStart,
      endIndex: values.length,
      slope: finalSegmentModel.slope,
      intercept: finalSegmentModel.intercept,
    });

    const fittedValues = this.buildPiecewiseValues(segments, values.length);

    return {
      values: fittedValues,
      breakIndex: breakIndices[0] ?? null,
      breakIndices,
      segments,
    };
  }

  private fitLinearRegression(values: number[], start: number, end: number): RegressionModel {
    const count = end - start;
    if (count <= 0) {
      return { slope: 0, intercept: 0 };
    }

    let sumX = 0;
    let sumY = 0;
    let sumXX = 0;
    let sumXY = 0;

    for (let x = 0; x < count; x += 1) {
      const y = values[start + x];
      sumX += x;
      sumY += y;
      sumXX += x * x;
      sumXY += x * y;
    }

    const denominator = count * sumXX - sumX * sumX;
    const slope = denominator === 0 ? 0 : (count * sumXY - sumX * sumY) / denominator;
    const intercept = (sumY - slope * sumX) / count;

    return {
      slope,
      intercept,
    };
  }

  private predict(model: RegressionModel, x: number): number {
    return model.slope * x + model.intercept;
  }

  private shouldBreakSegment(residual: number, predicted: number, options: TrendLineOptions): boolean {
    if (residual >= options.absoluteThreshold) {
      return true;
    }

    const percentBase = Math.max(options.minPercentBase, Math.abs(predicted));
    return residual >= percentBase * options.percentThreshold;
  }

  private buildPiecewiseValues(segments: TrendSegment[], length: number): number[] {
    const fittedValues = new Array<number>(length).fill(0);

    for (const segment of segments) {
      for (let index = segment.startIndex; index < segment.endIndex; index += 1) {
        const localX = index - segment.startIndex;
        fittedValues[index] = this.predict(segment, localX);
      }
    }

    return fittedValues;
  }

  private hasSustainedLevelShift(values: number[], breakIndex: number, options: TrendLineOptions): boolean {
    if (breakIndex < options.minSegmentLength || values.length - breakIndex < options.minSegmentLength) {
      return false;
    }

    const beforeSlice = values.slice(breakIndex - options.minSegmentLength, breakIndex);
    const afterSlice = values.slice(breakIndex, breakIndex + options.minSegmentLength);
    const beforeMedian = this.median(beforeSlice);
    const afterMedian = this.median(afterSlice);
    const levelDelta = Math.abs(afterMedian - beforeMedian);
    if (levelDelta >= options.absoluteThreshold) {
      return true;
    }

    const percentBase = Math.max(options.minPercentBase, Math.abs(beforeMedian));
    return levelDelta >= percentBase * options.percentThreshold;
  }

  private median(values: number[]): number {
    if (!values.length) {
      return 0;
    }

    const sorted = [...values].sort((a, b) => a - b);
    const middle = Math.floor(sorted.length / 2);
    if (sorted.length % 2 === 0) {
      return (sorted[middle - 1] + sorted[middle]) / 2;
    }
    return sorted[middle];
  }
}
