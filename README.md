# htec-drf-dx-datagrid
# Overview
This package provides easy integration between [Django REST framework](https://www.django-rest-framework.org) and [DevExtreme Data Grid](https://js.devexpress.com/Demos/WidgetsGallery/Demo/DataGrid/Overview/jQuery/Light/).
It handles grouping, paging, filtering, aggregating and ordering on serverside.
# In which case should you use htec-drf-dx-datagrid?
You have DevExtreme in the frontend and Django REST framework as the backend. And your data is too large to load at once, but you want use grouping and filtering.
# How it works?
Htec-drf-dx-datagrid supports devextreme load options in HTTP-request and returns data in format fully compatible with Data Grid. 
All you need is to replace classname "ModelViewSet" with "DxModelViewSet" in your django project
# Installation
pip install htec-drf-dx-datagrid
# Configuration
Define your ModelViewSet class inherits from DxModelViewSet:

```python
from htec_drf_dx_datagrid import DxModelViewSet


class MyModelViewSet(DxModelViewSet):
    serializer_class = MyModelSerializer
    queryset = MyModel.objects.all()
```
Also you can define ReadOnlyModelViewSet inherits from DxReadOnlyModelViewSet

```python
from htec_drf_dx_datagrid import DxModelViewSet


class MyReadOnlyModelViewSet(DxReadOnlyModelViewSet):
    serializer_class = MyModelSerializer
    queryset = MyModel.objects.all()
```
Example for React.js:
```jsx
const load = (loadOptions) => {
    return axios(`${my_url}`, {
            params: loadOptions
        }
    ).then((response) => response.data
    )
}

export default class Example extends PureComponent {
   state={
       store: new CustomStore({ load: load})
   }

    render() {
        return (<DataGrid
                    dataSource={this.state.store}
                    height={"100vh"}
                >
                    <RemoteOperations groupPaging={true}/>
                    <Scrolling mode={'virtual'}/>
                    <HeaderFilter visible={true} allowSearch={true}/>
                    <Paging defaultPageSize={40}/>
                    <Sorting mode={"multiple"}/>
                    <FilterRow visible={true}/>
                    <GroupPanel visible={true}/>
                    <Grouping autoExpandAll={false}/>
                    <Summary>
                        <TotalItem column={"id"} summaryType={"count"}/>
                        <GroupItem column={"name"} summaryType={"max"}/>
                    </Summary>
                </DataGrid>
        );
    }
}
``` 
Example for jQuery.js:
```js
        const load = (loadOptions) => {
            return axios(`${my_url}`, {
                    params: loadOptions
                }
            ).then((response) => response.data
            )
        }

        const store = new DevExpress.data.CustomStore({load: load});
        $("#gridContainer").dxDataGrid({
            dataSource: store,
            height: "100vh",
            remoteOperations: {
                groupPaging: true
            },
            scrolling: {mode: 'virtual'},
            headerFilter: {visible: true, allowSearch: true},
            paging: {defaultPageSize: 40},
            sorting: {mode: "multiple"},
            filterRow: {visible: true},
            groupPanel: {visible: true},
            grouping: {autoExpandAll: false},
            summary: {
                totalItems: [{
                    column: "id",
                    summaryType: "count"
                }],
                groupItems: [{
                    column: "id",
                    summaryType: "min"
                }]
            }
        });
```   
By default, filtering is case-sensitive.If you want case-insensitive behavior, you must set FILTER_CASE_SENSITIVE parameter to false in django settings:
```
REST_FRAMEWORK = {
    'DRF_DX_DATAGRID': {
        'FILTER_CASE_SENSITIVE': False}
}
```