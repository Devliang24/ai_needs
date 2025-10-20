import React from 'react';

import TestCasesView from './TestCasesView';

interface Props {
  data: Record<string, unknown>;
}

const SupplementalTestCasesView: React.FC<Props> = ({ data }) => {
  const modules = Array.isArray(data.modules) ? data.modules : [];

  return (
    <div style={{ marginTop: 16 }}>
      <TestCasesView
        data={{ modules }}
        title="补充测试用例"
        emptyText="暂无补充测试用例"
      />
    </div>
  );
};

export default SupplementalTestCasesView;
