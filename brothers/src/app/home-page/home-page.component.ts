import { Component, ElementRef, Input, ViewChild } from '@angular/core';
import { FileSelectEvent, FileUploadHandlerEvent, FileUploadModule } from "primeng/fileupload";
import { PreviewPageComponent } from '../preview-page/preview-page.component';
import { ActivatedRoute } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { EntityResponse } from "../response";
import { map } from 'rxjs';

@Component({
     selector: 'brothers-home',
     standalone: true,
     imports: [FileUploadModule, PreviewPageComponent],
     templateUrl: './home-page.component.html',
     styleUrl: './home-page.component.css'
})
export class HomePageComponent {
     @Input() upload_url!: string;
     @Input() download_url!: string;
     file_url!: string;

     uploaded: Array<File> = Array();
     response_url: string = '';
     show_preview: boolean = false;

     @ViewChild('canvas') canvas!: ElementRef<HTMLCanvasElement>;

     constructor(private route: ActivatedRoute, private http: HttpClient) {
          route.data.subscribe((data) => {
               this.upload_url = data['upload_url'];
               this.download_url = data['download_url'];
          })
     }

     on_file_upload() {
          this.show_preview = true;
     }

     on_file_select(event: FileSelectEvent) {
          this.uploaded = [...event.files];
          this.file_url = URL.createObjectURL(this.uploaded[0]);
     }

     upload_image(event: FileUploadHandlerEvent) {
          if (event.files.length) {
               this.on_file_upload();

               let file = event.files[0];
               let data = new FormData();
               data.append('file', file, file.name)
               this.http.post(this.upload_url, data)
                    .pipe(
                         map((value: Object) => value as EntityResponse)
                    )
                    .subscribe((response: EntityResponse) => {
                         this.response_url = `${this.download_url}${response.id}`
                    })
          }
     }
}
