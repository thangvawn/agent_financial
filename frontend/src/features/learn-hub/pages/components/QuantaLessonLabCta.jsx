import React from 'react';
import { useFinancialWorkflow } from '../../../../shared/context/FinancialWorkflowContext';

export default function QuantaLessonLabCta({ lessonTitle, demoCode }) {
  const { navigateToSimulationLab } = useFinancialWorkflow();

  const handleOpenStudio = () => {
    navigateToSimulationLab({
      ticker: 'FPT',
      strategyCode: demoCode || null,
      period: '1y',
      interval: '1d',
    });
  };

  return (
    <div className="my-5 rounded-lg border border-cyan-800/40 bg-gradient-to-r from-cyan-950/30 via-slate-900 to-slate-900 p-3.5 shadow-lg">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-sm">⚡</span>
            <span className="text-xs font-bold text-cyan-300">
              Thực Hành Thực Chiến Trong Quanta Studio
            </span>
          </div>
          <p className="mt-1 text-[11px] text-slate-400">
            Kiểm chứng ngay lý thuyết của bài học trên 15+ năm dữ liệu nến thật của TTCK Việt Nam.
          </p>
        </div>

        <button
          type="button"
          onClick={handleOpenStudio}
          className="inline-flex items-center gap-1.5 whitespace-nowrap rounded-md bg-gradient-to-r from-cyan-500 to-blue-600 px-3.5 py-2 text-xs font-semibold text-white shadow-md transition-all hover:from-cyan-400 hover:to-blue-500 active:scale-95"
        >
          <span>Mở Chạy Thử Ngay</span>
          <span>→</span>
        </button>
      </div>
    </div>
  );
}
