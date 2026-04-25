import React from 'react';
import { Radar } from 'lucide-react';
import type { FinalReport } from '@/types';

interface ReportSectionProps {
  report: FinalReport;
}

export function ReportSection({ report }: ReportSectionProps) {
  const maxScore = 100;

  return (
    <div className="space-y-4">
      {/* Overall Score */}
      <div className="text-center py-4">
        <div className="text-4xl font-bold mb-1">{report.score}</div>
        <div className="text-sm text-muted-foreground">综合评分</div>
      </div>

      {/* Radar Chart - Simplified */}
      <div className="h-40 relative">
        <svg viewBox="0 0 200 200" className="w-full h-full">
          {/* Background circles */}
          {[0.25, 0.5, 0.75, 1].map((ratio, i) => (
            <polygon
              key={i}
              points={getPolygonPoints(report.dimensions.length, ratio * 80, 100, 100)}
              fill="none"
              stroke="rgba(255,255,255,0.1)"
              strokeWidth="1"
            />
          ))}

          {/* Axis lines */}
          {report.dimensions.map((_, i) => {
            const angle = getAngle(i, report.dimensions.length);
            const x = 100 + 80 * Math.sin(angle);
            const y = 100 - 80 * Math.cos(angle);
            return (
              <line
                key={i}
                x1="100"
                y1="100"
                x2={x}
                y2={y}
                stroke="rgba(255,255,255,0.1)"
                strokeWidth="1"
              />
            );
          })}

          {/* Data polygon */}
          <polygon
            points={getDataPolygon(report.dimensions, 80, 100, 100)}
            fill="rgba(59, 130, 246, 0.3)"
            stroke="rgba(59, 130, 246, 0.8)"
            strokeWidth="2"
          />
        </svg>

        {/* Labels */}
        {report.dimensions.map((dim, i) => {
          const angle = getAngle(i, report.dimensions.length);
          const x = 100 + 95 * Math.sin(angle);
          const y = 100 - 95 * Math.cos(angle);
          return (
            <div
              key={dim.name}
              className="absolute text-xs transform -translate-x-1/2 -translate-y-1/2"
              style={{ left: `${x}%`, top: `${y}%` }}
            >
              <span className="bg-card px-1 rounded">{dim.name}</span>
            </div>
          );
        })}
      </div>

      {/* Dimensions */}
      <div className="space-y-2">
        {report.dimensions.map((dim) => (
          <div key={dim.name} className="flex items-center gap-2">
            <span className="text-sm w-16">{dim.name}</span>
            <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden">
              <div
                className="h-full bg-brand-500 rounded-full"
                style={{ width: `${(dim.score / maxScore) * 100}%` }}
              />
            </div>
            <span className="text-sm w-8 text-right">{dim.score}</span>
          </div>
        ))}
      </div>

      {/* Pros */}
      {report.pros.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-green-400 mb-2">✅ 优点</h4>
          <ul className="text-sm text-muted-foreground space-y-1">
            {report.pros.map((pro, i) => (
              <li key={i}>• {pro}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Cons */}
      {report.cons.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-red-400 mb-2">❌ 不足</h4>
          <ul className="text-sm text-muted-foreground space-y-1">
            {report.cons.map((con, i) => (
              <li key={i}>• {con}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Suggestions */}
      {(report.suggestions.must.length > 0 ||
        report.suggestions.should.length > 0 ||
        report.suggestions.optional.length > 0) && (
        <div>
          <h4 className="text-sm font-medium mb-2">💡 建议</h4>
          <div className="space-y-2">
            {report.suggestions.must.length > 0 && (
              <div>
                <span className="text-xs px-2 py-0.5 rounded bg-red-500/20 text-red-400 mr-2">
                  必须
                </span>
                <span className="text-sm text-muted-foreground">
                  {report.suggestions.must.join('、')}
                </span>
              </div>
            )}
            {report.suggestions.should.length > 0 && (
              <div>
                <span className="text-xs px-2 py-0.5 rounded bg-yellow-500/20 text-yellow-400 mr-2">
                  建议
                </span>
                <span className="text-sm text-muted-foreground">
                  {report.suggestions.should.join('、')}
                </span>
              </div>
            )}
            {report.suggestions.optional.length > 0 && (
              <div>
                <span className="text-xs px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 mr-2">
                  可选
                </span>
                <span className="text-sm text-muted-foreground">
                  {report.suggestions.optional.join('、')}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function getAngle(index: number, total: number): number {
  return (2 * Math.PI * index) / total - Math.PI / 2;
}

function getPolygonPoints(
  sides: number,
  radius: number,
  cx: number,
  cy: number
): string {
  const points: string[] = [];
  for (let i = 0; i < sides; i++) {
    const angle = getAngle(i, sides);
    const x = cx + radius * Math.cos(angle);
    const y = cy + radius * Math.sin(angle);
    points.push(`${x},${y}`);
  }
  return points.join(' ');
}

function getDataPolygon(
  dimensions: { score: number; name: string }[],
  maxRadius: number,
  cx: number,
  cy: number
): string {
  const points: string[] = [];
  for (let i = 0; i < dimensions.length; i++) {
    const angle = getAngle(i, dimensions.length);
    const radius = (dimensions[i].score / 100) * maxRadius;
    const x = cx + radius * Math.cos(angle);
    const y = cy + radius * Math.sin(angle);
    points.push(`${x},${y}`);
  }
  return points.join(' ');
}
