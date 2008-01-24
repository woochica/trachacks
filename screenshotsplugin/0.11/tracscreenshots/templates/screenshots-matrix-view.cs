<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:xi="http://www.w3.org/2001/XInclude" xmlns:py="http://genshi.edgewall.org/">
  <div class="images">
    <table>
      <tbody>
        <py:for each="row in screenshots.matrix">
          <tr>
            <py:for each="image in row">
              <td>
                <py:choose>
                  <div py:when="image.id != -1" class="image">
                    <a href="${href.screenshots(image.id)}" title="${image.id}">
                      <img src="${href.screenshots(image.id)}?width=${screenshots.width};height=${screenshots.height};format=raw"
                        alt="${image.description}" width="${screenshots.width}" height="${screenshots.height}"/>
                    </a>
                  </div>
                  <div py:otherwise="" class="image noimage" style="width: ${screenshots.width}px; height: ${screenshots.height}px">
                    &nbsp;
                  </div>
                </py:choose>
                <div py:if="'SCREENSHOTS_ADMIN' in perm" class="controls">
                  <py:choose>
                    <py:when test="image.id != -1">
                      <a href="${href.screenshots()}?action=edit;id=${image.id};index=${screenshots.index}">Edit</a>
                      <a href="${href.screenshots()}?action=delete;id=${image.id};index=${screenshots.index}">Delete</a>
                    </py:when>
                    <py:otherwise>
                      &nbsp;
                    </py:otherwise>
                  </py:choose>
                </div>
              </td>
            </py:for>
          </tr>
        </py:for>
      </tbody>
    </table>
  </div>

  <div class="controls">
    <py:choose>
      <py:when test="screenshots.prev_index != -1">
        <a href="${href.screenshots()}?index=${screenshots.prev_index}">&larr; Previous Page</a>
      </py:when>
      <py:otherwise>
        &larr; Previous Page
      </py:otherwise>
    </py:choose>
    &nbsp;${screenshots.page}/${screenshots.page_count}&nbsp;
    <py:choose>
      <py:when test="screenshots.next_index != -1">
        <a href="${href.screenshots()}?index=${screenshots.next_index}">Next Page &rarr;</a>
      </py:when>
      <py:otherwise>
        Next Page &rarr;
      </py:otherwise>
    </py:choose>
  </div>
</html>
