import type { App, Plugin } from 'vue'
import { ElButton } from 'element-plus/es/components/button/index.mjs'
import { ElContainer, ElAside, ElHeader, ElMain } from 'element-plus/es/components/container/index.mjs'
import { ElDatePicker } from 'element-plus/es/components/date-picker/index.mjs'
import { ElDialog } from 'element-plus/es/components/dialog/index.mjs'
import { ElEmpty } from 'element-plus/es/components/empty/index.mjs'
import { ElForm, ElFormItem } from 'element-plus/es/components/form/index.mjs'
import { ElIcon } from 'element-plus/es/components/icon/index.mjs'
import { ElInput } from 'element-plus/es/components/input/index.mjs'
import { vLoading } from 'element-plus/es/components/loading/index.mjs'
import { ElMenu, ElMenuItem } from 'element-plus/es/components/menu/index.mjs'
import { ElPagination } from 'element-plus/es/components/pagination/index.mjs'
import { ElRadio, ElRadioGroup } from 'element-plus/es/components/radio/index.mjs'
import { ElSelect, ElOption, ElOptionGroup } from 'element-plus/es/components/select/index.mjs'
import { ElTag } from 'element-plus/es/components/tag/index.mjs'

import 'element-plus/es/components/aside/style/css'
import 'element-plus/es/components/button/style/css'
import 'element-plus/es/components/container/style/css'
import 'element-plus/es/components/date-picker/style/css'
import 'element-plus/es/components/dialog/style/css'
import 'element-plus/es/components/empty/style/css'
import 'element-plus/es/components/form/style/css'
import 'element-plus/es/components/form-item/style/css'
import 'element-plus/es/components/header/style/css'
import 'element-plus/es/components/icon/style/css'
import 'element-plus/es/components/input/style/css'
import 'element-plus/es/components/loading/style/css'
import 'element-plus/es/components/main/style/css'
import 'element-plus/es/components/menu/style/css'
import 'element-plus/es/components/menu-item/style/css'
import 'element-plus/es/components/message/style/css'
import 'element-plus/es/components/message-box/style/css'
import 'element-plus/es/components/option/style/css'
import 'element-plus/es/components/pagination/style/css'
import 'element-plus/es/components/radio/style/css'
import 'element-plus/es/components/radio-group/style/css'
import 'element-plus/es/components/select/style/css'
import 'element-plus/es/components/tag/style/css'

const components = [
  ['ElAside', ElAside],
  ['ElButton', ElButton],
  ['ElContainer', ElContainer],
  ['ElDatePicker', ElDatePicker],
  ['ElDialog', ElDialog],
  ['ElEmpty', ElEmpty],
  ['ElForm', ElForm],
  ['ElFormItem', ElFormItem],
  ['ElHeader', ElHeader],
  ['ElIcon', ElIcon],
  ['ElInput', ElInput],
  ['ElMain', ElMain],
  ['ElMenu', ElMenu],
  ['ElMenuItem', ElMenuItem],
  ['ElOption', ElOption],
  ['ElOptionGroup', ElOptionGroup],
  ['ElPagination', ElPagination],
  ['ElRadio', ElRadio],
  ['ElRadioGroup', ElRadioGroup],
  ['ElSelect', ElSelect],
  ['ElTag', ElTag]
] as const

const elementPlusPlugin: Plugin = {
  install(app: App) {
    for (const [name, component] of components) {
      app.component(name, component)
    }

    app.directive('loading', vLoading)
  }
}

export default elementPlusPlugin