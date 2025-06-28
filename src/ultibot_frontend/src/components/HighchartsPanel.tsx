import React from 'react';
import Highcharts from 'highcharts';
import HighchartsReact from 'highcharts-react-official';

const options: Highcharts.Options = {
  title: {
    text: 'Gráfico de Prueba'
  },
  series: [{
    type: 'line',
    data: [1, 2, 3, 4, 5]
  }]
};

const HighchartsPanel: React.FC = () => {
  return (
    <div className="h-full w-full">
      <HighchartsReact
        highcharts={Highcharts}
        options={options}
        containerProps={{ style: { height: "100%" } }}
      />
    </div>
  );
}

export default HighchartsPanel;
