export const DEPARTMENTS = [
  { code: 'TECH', name: 'Tech' },
  { code: 'FINANCE', name: 'Finance' },
  { code: 'SALES', name: 'Sales' },
  { code: 'CUSTOMER_SUPPORT', name: 'Customer Support' },
  { code: 'SECURITY', name: 'Security' },
  { code: 'CATERING', name: 'Catering' },
  { code: 'MARKETING', name: 'Marketing' },
  { code: 'ADMINISTRATION', name: 'Administration/Management' },
]

const departmentNameByKey = new Map(
  DEPARTMENTS.flatMap(({ code, name }) => [
    [code.replaceAll(/[^a-z0-9]/gi, '').toLowerCase(), name],
    [name.replaceAll(/[^a-z0-9]/gi, '').toLowerCase(), name],
  ]),
)

for (const alias of [
  'Technology',
  'IT',
  'Information Technology',
  'Accounting',
  'Finance and Accounting',
  'Customer Service',
  'Customer Services',
  'Admin',
  'Management',
  'Administration and Management',
]) {
  const key = alias.replaceAll(/[^a-z0-9]/gi, '').toLowerCase()
  const target = alias === 'Technology' || alias === 'IT'
    ? 'Tech'
    : alias === 'Accounting'
      ? 'Finance'
      : alias.startsWith('Customer')
        ? 'Customer Support'
        : 'Administration/Management'
  departmentNameByKey.set(key, target)
}

export const getDepartmentName = value => {
  const key = String(value ?? '').trim().replaceAll(/[^a-z0-9]/gi, '').toLowerCase()
  if (!key || key === 'undefined' || key === 'null') return null
  return departmentNameByKey.get(key) || null
}
