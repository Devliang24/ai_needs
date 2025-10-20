import { ConfigProvider, Layout } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import React from 'react';

import { HomePage } from './pages';

const { Content } = Layout;

const App: React.FC = () => {
  return (
    <ConfigProvider locale={zhCN}>
      <Layout style={{ height: '100vh' }}>
        <Content style={{ height: '100%' }}>
          <HomePage />
        </Content>
      </Layout>
    </ConfigProvider>
  );
};

export default App;
