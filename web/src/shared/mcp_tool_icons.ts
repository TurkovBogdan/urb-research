import {
  IconList,
  IconSearch,
  IconEye,
  IconPlus,
  IconPencil,
  IconRefresh,
  IconDeviceFloppy,
  IconTrash,
  IconPlayerPlay,
  IconUpload,
  IconDownload,
  IconTool,
  IconMessages,
  IconBulb,
  IconRobot,
  IconMail,
  IconWorld,
  IconUsers,
  IconBuildingStore,
  IconServerBolt,
} from '@tabler/icons-vue'
import type { Component } from 'vue'

// Возвращаем как `any` чтобы устроить Vuetify `IconValue` (Component-типы
// @tabler/icons-vue не совпадают по сигнатуре с тем, что ожидает VIcon).

// Сопоставление tool-имени с иконкой по ключевому слову в имени.
// Имена в MCP обычно snake_case: `tech_list`, `skill_upsert`, `run_query`, …
const RULES: { match: RegExp; icon: Component }[] = [
  { match: /(^|[_.\-])list($|[_.\-])|(^|[_.\-])index($|[_.\-])/i, icon: IconList },
  { match: /(^|[_.\-])search($|[_.\-])|(^|[_.\-])find($|[_.\-])|(^|[_.\-])query($|[_.\-])/i, icon: IconSearch },
  { match: /(^|[_.\-])get($|[_.\-])|(^|[_.\-])read($|[_.\-])|(^|[_.\-])show($|[_.\-])|(^|[_.\-])view($|[_.\-])/i, icon: IconEye },
  { match: /(^|[_.\-])create($|[_.\-])|(^|[_.\-])add($|[_.\-])|(^|[_.\-])new($|[_.\-])/i, icon: IconPlus },
  { match: /(^|[_.\-])update($|[_.\-])|(^|[_.\-])modify($|[_.\-])|(^|[_.\-])edit($|[_.\-])|(^|[_.\-])set($|[_.\-])/i, icon: IconRefresh },
  { match: /(^|[_.\-])upsert($|[_.\-])|(^|[_.\-])save($|[_.\-])|(^|[_.\-])put($|[_.\-])/i, icon: IconDeviceFloppy },
  { match: /(^|[_.\-])delete($|[_.\-])|(^|[_.\-])remove($|[_.\-])|(^|[_.\-])drop($|[_.\-])/i, icon: IconTrash },
  { match: /(^|[_.\-])run($|[_.\-])|(^|[_.\-])exec($|[_.\-])|(^|[_.\-])execute($|[_.\-])|(^|[_.\-])call($|[_.\-])/i, icon: IconPlayerPlay },
  { match: /(^|[_.\-])upload($|[_.\-])|(^|[_.\-])send($|[_.\-])|(^|[_.\-])post($|[_.\-])/i, icon: IconUpload },
  { match: /(^|[_.\-])download($|[_.\-])|(^|[_.\-])fetch($|[_.\-])|(^|[_.\-])pull($|[_.\-])/i, icon: IconDownload },
  { match: /(^|[_.\-])write($|[_.\-])|(^|[_.\-])patch($|[_.\-])/i, icon: IconPencil },
]

export function toolIcon(name: string): any {
  for (const { match, icon } of RULES) {
    if (match.test(name)) return icon
  }
  return IconTool
}

// Тематическая иконка MCP-сервера по его коду (keyword-match по коду сервера).
const SERVER_RULES: { match: RegExp; icon: Component }[] = [
  { match: /insight/i, icon: IconBulb },
  { match: /conversation|chat|message/i, icon: IconMessages },
  { match: /llm|model|provider|agent/i, icon: IconRobot },
  { match: /mail|email/i, icon: IconMail },
  { match: /geo|country|location/i, icon: IconWorld },
  { match: /user|contact|team/i, icon: IconUsers },
  { match: /twenty|crm|company/i, icon: IconBuildingStore },
]

export function serverIcon(code: string): any {
  for (const { match, icon } of SERVER_RULES) {
    if (match.test(code)) return icon
  }
  return IconServerBolt
}
