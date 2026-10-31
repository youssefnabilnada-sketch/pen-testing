import {render,screen,cleanup,fireEvent} from '@testing-library/react';
import {afterEach,it,expect} from 'vitest';
import RetestComparison from '../app/console/RetestComparison';
import {Experience} from '../app/console/Experience';
afterEach(()=>{cleanup();localStorage.clear()});
it('distinguishes missing results from measured zero findings',()=>{render(<RetestComparison comparison={{resolved:[],unresolved:['x']}}/>);expect(screen.getByText('0')).toBeTruthy();expect(screen.getByText('1')).toBeTruthy();expect(screen.getAllByText('—')).toHaveLength(2);expect(screen.getAllByText('Result not available')).toHaveLength(2);});
it('shows Arabic limitations without claiming whole-site security',()=>{render(<Experience><RetestComparison comparison={{resolved:['x'],unverified:[]}}/></Experience>);fireEvent.click(screen.getByRole('button',{name:'التبديل إلى العربية'}));expect(screen.getByRole('region',{name:'مقارنة إعادة الفحص'})).toBeTruthy();expect(screen.getByText(/ولا يضمن خلو الموقع/)).toBeTruthy();});
