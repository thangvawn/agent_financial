import { Moon, Sun } from 'lucide-react'
import { useTheme } from './appTheme'

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme()
  return <button type="button" className="theme-toggle" role="switch" aria-checked={theme === 'dark'}
    aria-label="Chế độ tối" title={theme === 'dark' ? 'Chuyển sang giao diện sáng' : 'Chuyển sang giao diện tối'} onClick={toggleTheme}>
    {theme === 'dark' ? <Moon size={16} aria-hidden="true" /> : <Sun size={16} aria-hidden="true" />}
    <span>{theme === 'dark' ? 'Tối' : 'Sáng'}</span>
  </button>
}
