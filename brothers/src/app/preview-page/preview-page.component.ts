import { AfterViewChecked, Component, ElementRef, Input, ViewChild } from '@angular/core';
import { CommonModule } from "@angular/common";
import { HttpClient } from '@angular/common/http';
import { first, interval, map, switchMap, takeWhile } from 'rxjs';
import { DialogModule } from "primeng/dialog";
import { ButtonModule } from "primeng/button";
import { EntityResponse, Result } from "../response";

@Component({
    selector: 'brother-preview',
    standalone: true,
    imports: [CommonModule, ButtonModule, DialogModule],
    templateUrl: './preview-page.component.html',
    styleUrl: './preview-page.component.css'
})
export class PreviewPageComponent implements AfterViewChecked {
    @Input({ required: true }) file!: string;
    @Input({ required: true }) url!: string;
    @ViewChild('canvas') canvas!: ElementRef<HTMLCanvasElement>;
    space = {
        width: screen.height,
        height: screen.height
    };
    canvas_space = {
        width: 0.8 * screen.width,
        height: 0.8 * screen.height
    };
    show_retry_dialog: boolean = false;
    retry_dialog_title: string = '';
    header_message: string | null = null;
    header_color?: string;

    private image: HTMLImageElement = new Image();
    private x_offset: number = 0;
    private y_offset: number = 0;
    private ratio: number = 1.0;

    constructor(private http: HttpClient) {
        this.image.onload = (_) => {
            this.ratio = Math.min((0.8 * screen.width) / this.image.width, (0.8 * screen.height) / this.image.height, 1.0);

            let width = this.ratio * this.image.width;
            let height = this.ratio * this.image.height;

            this.x_offset = Math.round((this.canvas_space.width - width) / 2);
            this.y_offset = Math.round((this.canvas_space.height - height) / 2);

            let context = this.canvas.nativeElement.getContext('2d');
            context?.drawImage(this.image, this.x_offset, this.y_offset, width, height)
        }
    }

    private poll_results() {
        const timeout = 2000;
        const max_retries = 30;
        let retry = 0;

        interval(timeout)
            .pipe(
                switchMap(() => this.http.get(this.url, { responseType: "json" })),
                takeWhile(() => retry++ < max_retries, true),
                map((value: Object) => value as EntityResponse),
                first(response => response.status === "processed", undefined)
            )
            .subscribe(
                {
                    next: (response?: EntityResponse) => {
                        if (response === undefined) {
                            this.show_retry_dialog = true;
                            this.retry_dialog_title = 'Number of retries exceeded. Would you like to try again?';
                        }
                        else if (response.results.length > 0) {
                            this.header_message = 'Your keys have been found!';
                            this.header_color = "green"
                            this.draw_bounds(response.results);
                        } else {
                            this.header_message = 'No keys have been found on image.';
                            this.header_color = "red"
                        }
                    },
                    error: (_) => {
                        this.show_retry_dialog = true;
                        this.retry_dialog_title = 'Error occured. Would you like to retry?'
                    },
                    complete: () => {}
                }
            )
    }

    retry() {
        this.show_retry_dialog = false;
        this.poll_results();
    }

    cancel() {
        this.show_retry_dialog = false;
        // TODO: Navigate back to Home Page
    }

    private draw_bounds(bounds: Array<Result>) {
        let context = this.canvas.nativeElement.getContext('2d');
        if (!context) {
            return;
        }

        bounds.forEach(result => {
            context.font = '24px Roboto';
            context.strokeStyle = '#7cff36';
            context.lineWidth = 4;
            
            result.x = result.x * this.ratio
            result.y = result.y * this.ratio
            result.w = result.w * this.ratio
            result.h = result.h * this.ratio
            
            context.strokeRect(this.x_offset + result.x, this.y_offset + result.y, result.w, result.h);
            context.fillStyle = 'white';
            context.fillRect(this.x_offset + result.x + 4, this.y_offset + result.y + 4, context.measureText(result.label).width + 20, 30);
            context.fillStyle = 'black';
            context.fillText(result.label, this.x_offset + result.x + 10, this.y_offset + result.y + 25)
        });
    }

    // AfterViewChecked Interface

    ngAfterViewChecked(): void {
        if (this.image.src !== this.file) {
            this.image.src = this.file;
            this.poll_results();
        }
    }
}
