import { Routes } from '@angular/router';
import { HomePageComponent } from './home-page/home-page.component';

export const routes: Routes = [
    {
        path: '',
        component: HomePageComponent,
        data: {
            upload_url: 'http://127.0.0.1:7071/api/debug/entities',
            download_url: 'http://127.0.0.1:7071/api/debug/entities/'
        }
    }
];
